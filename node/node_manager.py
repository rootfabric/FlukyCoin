import time
import threading
import datetime
import signal

from core.Block import Block
from core.Transactions import Transaction
from core.protocol import Protocol
from storage.mempool import Mempool
from storage.miners_storage import MinerStorage
from storage.chain import Chain
from tools.time_sync import NTPTimeSynchronizer
from tools.logger import Log
from concurrent.futures import ThreadPoolExecutor
from net.GrpcServer import GrpcServer
from net.ConnectManager import ConnectManager
from net.ClientHandler import ClientHandler
from node.sync_manager import SyncManager


class NodeManager:
    def __init__(self, config, log=Log()):
        self.log = log
        self.config = config
        self.start_time = time.time()
        self.initial_peers = config.get("initial_peers", ["localhost:5555"])
        self.version = Protocol.VERSION

        self.time_ntpt = NTPTimeSynchronizer(log=log)

        # хранилища
        self.mempool = Mempool(config, self)
        self.miners_storage = MinerStorage(config)

        self.chain = Chain(config=self.config, mempool=self.mempool, log=self.log)

        # связь
        self.server = GrpcServer(self.config, self)
        self.client_handler = ClientHandler(self.server.servicer, self)
        self.server.start()

        self.connect_manager = ConnectManager(self.server.get_external_host_ip(), known_peers=set(self.initial_peers))

        # синхронизация нод
        self.sync_manager = SyncManager(self,  log)


        # флаг необходимости сделать рассылку нового кандидата
        self.need_distribute_candidate = False


        self.timer_last_distribute = 0
        self.timer_drop_synced = None
        self.running = True

        self.system_executor = ThreadPoolExecutor(max_workers=5)
        self.executor = ThreadPoolExecutor(max_workers=100)

        # переменные для дебага
        self.enable_load_info = True
        self.enable_distribute_block = True

        # для отключения
        self.shutdown_event = threading.Event()
        signal.signal(signal.SIGINT, self.signal_handler)
        signal.signal(signal.SIGTERM, self.signal_handler)

    def signal_handler(self, signum, frame):
        self.log.info("Signal received, shutting down...")
        self.shutdown_event.set()
        self.running = False
        self.executor.shutdown(wait=False)
        self.system_executor.shutdown(wait=False)
        self.sync_manager.signal_handler(signum, frame)

    def is_synced(self):
        return self.sync_manager.is_synced()

    def set_node_synced(self, state):
        self.sync_manager.set_node_synced(state)

    def add_transaction_to_mempool(self, transaction):
        if not self.mempool.check_hash_transaction(transaction.txhash):
            self.mempool.add_transaction(transaction)

    def add_new_transaction(self, transaction: Transaction):
        if not self.mempool.check_hash_transaction(transaction.txhash):
            if not self.chain.validate_transaction(transaction):
                self.log.info("Транзакция отклонена", transaction.txhash)
                return
            self.add_transaction_to_mempool(transaction)
            self.executor.submit(self.client_handler.distribute_transaction_hash, transaction.txhash)
            self.log.info("New transaction added and hash distributed.")

    def create_block(self, address_reward=None):
        last_block = self.chain.block_candidate
        if last_block is not None and last_block.signer in self.miners_storage.keys:
            return None

        for miner_address in list(self.miners_storage.keys.keys()):
            for address_miner in self.miners_storage.keys.keys():
                if self.chain.try_address_candidate(address_miner, miner_address):
                    miner_address = address_miner

            if last_block is not None:
                if self.chain.try_address_candidate(last_block.signer, miner_address):
                    return None

            if last_block is not None and miner_address == last_block.signer:
                return None

            if miner_address in self.miners_storage.keys and self.miners_storage.keys[miner_address].count_sign() <= 0:
                self.miners_storage.close_key(miner_address)
                continue

            if miner_address not in self.miners_storage.keys:
                continue

            xmss = self.miners_storage.keys[miner_address]
            next_idx = self.chain.next_address_nonce(miner_address)
            if xmss.keyPair.SK.idx != next_idx - 1:
                edited_idx = xmss.set_idx(next_idx - 1)

            last_block_time = self.chain.last_block().timestamp_seconds if self.chain.last_block() is not None else self.chain.time()
            time_candidat = last_block_time + Protocol.BLOCK_TIME_SECONDS
            block_timestamp_seconds = time_candidat if time_candidat > self.chain.time() else self.chain.time()


            # берутся все транзакции без разбора
            transactions = []
            for tr in list(self.mempool.transactions.values()):
                if self.chain.validate_transaction(tr):
                    transactions.append(tr)

                self.mempool.remove_transaction(tr.txhash)


            block_candidate = Block.create(self.chain.blocks_count(), self.chain.last_block_hash(),
                                           block_timestamp_seconds, transactions, address_miner=xmss.address,
                                           address_reward=address_reward)

            block_candidate.make_sign(xmss)

            if not self.chain.validate_block(block_candidate):
                xmss.set_idx(xmss.idx() - 1)
                block_candidate = None
            else:
                self.miners_storage.save_storage_to_disk(block_candidate)

            return block_candidate

        miners_storage_size = self.config.get('miners_storage_size', 10)
        miners_storage_height =  self.config.get('miners_storage_height', 10)
        self.miners_storage.generate_keys(size = miners_storage_size, height=miners_storage_height)
        return None

    def uptime(self):
        return time.time() - self.start_time

    def toggle_feature(self):
        while True:
            command = input("Enter command: ").strip().split()
            if len(command) == 1:
                if command[0] == "1":
                    self.enable_load_info = not self.enable_load_info
                    self.log.info(f"enable_load_info {'enabled' if self.enable_load_info else 'disabled'}.")
                elif command[0] == "2":
                    self.enable_distribute_block = not self.enable_distribute_block
                    self.log.info(f"enable_distribute_block {'enabled' if self.enable_distribute_block else 'disabled'}.")
                else:
                    self.log.info(f"No such feature: {command[1]}")
            elif command[0] == "exit":
                self.log.info("Exiting...")
                break
            else:
                self.log.info("Unknown command.")

    def run_node(self):
        self.system_executor.submit(self.sync_manager.technical_block)
        self.system_executor.submit(self.sync_manager.sync_block)

        while self.running:
            if not self.sync_manager.is_synced():
                self.log.info(
                    f"---synced {self.sync_manager.is_synced()}-------is_miner {self.config.get('is_miner', 'False')}-----------active_peers: {self.server.servicer.active_peers}")

            if not self.sync_manager.is_synced():
                time.sleep(Protocol.BLOCK_TIME_INTERVAL_LOG)
                continue

            new_block = None

            if self.config.get('is_miner', "False"):
                last_block_time = self.chain.last_block().timestamp_seconds if self.chain.last_block() is not None else self.chain.time()
                if self.chain.blocks_count() == 0 or self.chain.time() > last_block_time + self.config.get('pause_before_try_block', Protocol.BLOCK_TIME_PAUSE_AFTER_CLOSE):
                    t = datetime.datetime.now()
                    new_block = self.create_block(self.config.get("address_reward"))
                    if new_block is not None:
                        self.log.info("Создание своего блока ", datetime.datetime.now() - t)

            if self.chain.add_block_candidate(new_block):
                self.log.info(f"Свой Блок кандидат добавлен", new_block.hash,
                              new_block.signer)
                self.need_distribute_candidate = True

            # центральная тока для рассылки кандидата на другие ноды
            if self.need_distribute_candidate and self.enable_distribute_block or time.time()>self.timer_last_distribute + 3:
                    self.timer_last_distribute = time.time()
                    self.executor.submit(self.client_handler.distribute_block, self.chain.block_candidate)
                    # self.client_handler.distribute_block(self.chain.block_candidate)
                    self.need_distribute_candidate = False

            needClose = self.chain.need_close_block()
            if needClose and self.chain.block_candidate is not None:
                num_block_to_close = self.chain.blocks_count() + 1
                self.log.info(f"*** START CLOSE {num_block_to_close} ****************")
                if not self.chain.close_block():
                    self.log.info("last_block", self.chain.last_block_hash())
                    self.log.info("candidate", self.chain.block_candidate_hash)
                    self.chain.reset_block_candidat()
                    continue
                last_block = self.chain.last_block()
                if last_block is not None:
                    self.log.info(f"Chain {self.chain.blocks_count()} blocks , последний: ", last_block.hash_block(),
                                  last_block.signer, self.chain.next_address_nonce(last_block.signer))

                # self.chain.save_chain_to_disk()
                self.miners_storage.save_storage_to_disk()
                self.mempool.save_mempool()

                self.log.info(f"{datetime.datetime.now()} Дата закрытого блока: {self.chain.last_block().datetime()}")
                # if Protocol.is_key_block(self.chain.last_block().hash):
                #     self.log.info("СЛЕДУЮЩИЙ КЛЮЧЕВОЙ БЛОК")
                self.log.info(
                    f"*** END CLOSE {num_block_to_close} **************** Active peers: {self.server.servicer.active_peers}")

            text = f"Check: {self.chain.blocks_count()} peers[{len(self.server.servicer.active_peers)}] txs[{self.mempool.size()}] "
            if self.chain.block_candidate is not None:
                text += f"delta: {self.chain.block_candidate.timestamp_seconds - self.chain.time():0.2f}  {self.chain.block_candidate.hash_block()[:5]}...{self.chain.block_candidate.hash_block()[-5:]}  singer: ...{self.chain.block_candidate.signer[-5:]}"
            self.log.info(text)

            time.sleep(Protocol.BLOCK_TIME_INTERVAL_LOG)
