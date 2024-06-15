# sync_manager.py
import time
import threading
from tools.logger import Log
from core.Block import Block
from core.protocol import Protocol

class SyncManager:
    def __init__(self, node_manager, log=Log()):
        self.node_manager = node_manager
        self.log = log
        self._synced = False
        self.timer_drop_synced = None
        self.running = True
        self.unsync_count = 0
        self.shutdown_event = threading.Event()

    def signal_handler(self, signum, frame):
        self.log.info("Signal received, shutting down...")
        self.shutdown_event.set()
        self.running = False

    def is_synced(self):
        return self._synced

    def set_node_synced(self, state):
        self._synced = state
        self.log.info(f"Node sync is {self._synced}")

    def check_sync(self, peer_info):
        """ проверка синхронности ноды """
        drop_sync_signal = False
        count_sync = 0

        if not self._synced:
            for address, info in peer_info.items():
                if info is None:
                    continue
                if info.synced:
                    count_sync += 1
                    if info.blocks > self.node_manager.chain.blocks_count():
                        drop_sync_signal = True
                        block_number_to_load = self.node_manager.chain.blocks_count()
                        block = self.node_manager.client_handler.get_block_by_number(block_number_to_load, info.network_info)
                        if self.node_manager.chain.validate_and_add_block(block):
                            self.log.info(f"Block [{block_number_to_load + 1}/{info.blocks}] added {block.hash_block()}")
                            if self.node_manager.chain.blocks_count() % 100 == 0:
                                self.log.info("Save chain")
                                self.node_manager.chain.save_chain_to_disk()
                        else:
                            self.log.info(f"{block_number_to_load + 1} reset")
                            self.node_manager.chain.drop_last_block()
                            self.node_manager.chain.drop_last_block()

        if self._synced and drop_sync_signal and self.timer_drop_synced is not None:
            self.timer_drop_synced = time.time()
            self.log.info("Включен таймер потери синхронизации")

        if count_sync == 0 and not self._synced and time.time() > self.node_manager.start_time + Protocol.TIME_WAIN_CONNECT_TO_NODES_START:
            self.log.info("Ноды не найдены, включаем синхронизацию")
            self.set_node_synced(True)

        if count_sync > 0 and len(peer_info) > 1 and not drop_sync_signal and not self._synced:
            self.timer_drop_synced = None
            last_block_time = self.node_manager.chain.last_block().timestamp_seconds if self.node_manager.chain.last_block() is not None else self.node_manager.chain.time()
            if self.node_manager.chain.time() > last_block_time + Protocol.BLOCK_START_CHECK_PAUSE and self.node_manager.chain.time() < last_block_time + Protocol.BLOCK_TIME_INTERVAL / 2:
                self.log.info("Нода синхронизирована")
                self.set_node_synced(True)
            else:
                self.log.info("Ждем начала блока")
                time.sleep(0.5)

        if self._synced:
            self.unsync_count = 0
            last_block_time = self.node_manager.chain.last_block().timestamp_seconds if self.node_manager.chain.last_block() is not None else self.node_manager.chain.time()
            if self.node_manager.chain.time() > last_block_time + Protocol.BLOCK_START_CHECK_PAUSE:
                for address, info in peer_info.items():
                    if not self.is_valid_peer_info(info):
                        continue
                    if self.is_block_candidate_new(info):
                        self.node_manager.client_handler.request_block_candidate_from_peer(info.network_info)

    def is_valid_peer_info(self, info):
        if info is None:
            return False
        if not info.synced:
            return False
        if info.block_candidate == 'None':
            return False
        if info.blocks != self.node_manager.chain.blocks_count():
            self.log.info("Различие в длине цепи", info.blocks, self.node_manager.chain.blocks_count())
            return False
        if info.latest_block != self.node_manager.chain.last_block_hash():
            self.log.info("Различие в блоках", info.latest_block, self.node_manager.chain.last_block_hash())
            self.unsync_count += 1
            return False
        return True

    def is_block_candidate_new(self, info):
        if info.block_candidate != self.node_manager.chain.block_candidate_hash and info.block_candidate not in self.node_manager.chain.history_hash:
            return True
        return False

    def sync_block(self):
        """ блок синхронизации """
        while self.running:
            try:
                if self.node_manager.enable_load_info:
                    self.check_sync(self.node_manager.peer_info)
                if self.is_synced():
                    time.sleep(1)
            except Exception as e:
                self.log.error('sync_block', e)

    def technical_block(self):
        timer_get_nodes = 0
        timer_ping_peers = 0

        while self.running:
            try:
                pause_ping = Protocol.TIME_PAUSE_PING_PEERS_SYNCED if self.is_synced() else Protocol.TIME_PAUSE_PING_PEERS_NOT_SYNCED
                if timer_ping_peers + pause_ping < time.time():
                    timer_ping_peers = time.time()
                    self.node_manager.client_handler.ping_peers()
                    try:
                        self.node_manager.client_handler.connect_to_peers()
                    except Exception as e:
                        self.log.error("error connect_to_peers", e)

                    if self.node_manager.enable_load_info:
                        self.node_manager.peer_info = self.node_manager.client_handler.fetch_info_from_peers()

                if self._synced and timer_get_nodes + pause_ping < time.time():
                    timer_get_nodes = time.time()
                    self.node_manager.client_handler.get_peers_list()
                    self.node_manager.client_handler.fetch_transactions_from_all_peers()

                if not self._synced:
                    continue

                time.sleep(1)
            except KeyboardInterrupt:
                self.running = False
                exit()
            except Exception as e:
                self.log.error("Ошибка технического блока ", e)
                self.running = False
