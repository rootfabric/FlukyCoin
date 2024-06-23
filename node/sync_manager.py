# sync_manager.py
import datetime
import time
import threading
from tools.logger import Log
from core.protocol import Protocol
from collections import defaultdict


class SyncManager:
    def __init__(self, node_manager, log=Log()):
        self.node_manager = node_manager
        self.log = log
        self._synced = False
        self.timer_drop_synced = None
        self.running = True
        self.unsync_count = 0
        self.shutdown_event = threading.Event()

        self.peer_info = {}

        # количество блоков в которых нода находится в рассинхроне с основной группой
        self.count_unsync_block = 0

    def signal_handler(self, signum, frame):
        self.log.info("Signal received, shutting down...")
        self.shutdown_event.set()
        self.running = False

    def is_synced(self):
        return self._synced

    def set_node_synced(self, state):
        self._synced = state
        self.log.info(f"Node sync is {self._synced}")

    def take_max_chain(self, peer_info):
        """Поиск нод с максимальной длиной, с которыми нужно синхронизироваться"""
        # Группировка пиров по количеству блоков и сложности сети
        chain_groups = defaultdict(list)

        for address, info in peer_info.items():
            if info and info.synced:
                chain_groups[(info.blocks, info.difficulty)].append(address)

        # Найти группу с максимальным количеством одинаковых элементов
        max_group_key = None
        max_group = []

        for key, group in chain_groups.items():
            if len(group) > len(max_group) or (
                    len(group) == len(max_group) and (max_group_key is None or key[1] > max_group_key[1])):
                max_group_key = key
                max_group = group

        if max_group_key:
            max_blocks, max_difficulty = max_group_key
        else:
            max_blocks, max_difficulty = 0, 0

        # if not self.node_manager.is_synced():
        #     self.log.info(f"Max chain group: {max_group} with {max_blocks} blocks and difficulty {max_difficulty}")

        return max_group, max_blocks, max_difficulty

    def check_info_for_candidate(self, peer_info):
        """ Проверяем ноды, информацию о кандидатах """

        if self.node_manager.chain.block_candidate is None:
            return

        max_group, max_blocks, max_difficulty = self.take_max_chain(peer_info)

        if self._synced:
            for address, info in peer_info.items():
                if info is None:
                    continue

                """ Берем блоки у максимальной цепи """
                if address not in max_group:
                    continue
                if max_blocks != info.blocks:
                    continue

                if info.difficulty != max_difficulty:
                    continue

                if info.blocks != self.node_manager.chain.blocks_count():
                    continue

                if info.block_candidate != self.node_manager.chain.block_candidate.hash_block():
                    """ Отличие блока, берем с ноды для проверки """
                    # если блок не хранится в кеше, то делаем запрос
                    if info.block_candidate is not None and self.node_manager.chain.check_hash(
                            info.block_candidate) is None and info.block_candidate != "None":
                        self.log.info(f"Get candidate {info.block_candidate} from {address}  ")
                        self.node_manager.client_handler.request_block_candidate_from_peer(address)

    def check_sync(self, peer_info):
        """ Проверка синхронности ноды """
        drop_sync_signal = False
        count_sync = 0

        max_group, max_blocks, max_difficulty = self.take_max_chain(peer_info)

        if not self._synced:
            for address, info in peer_info.items():
                if info is None:
                    continue

                """ Берем блоки у максимальной цепи """
                if address not in max_group:
                    continue
                if max_blocks != info.blocks:
                    continue

                if info.difficulty != max_difficulty:
                    continue

                if info.synced:
                    count_sync += 1
                    if info.blocks > self.node_manager.chain.blocks_count():
                        drop_sync_signal = True
                        block_number_to_load = self.node_manager.chain.blocks_count()

                        block = self.node_manager.client_handler.get_block_by_number(block_number_to_load,
                                                                                     info.network_info)
                        t = datetime.datetime.now()
                        if self.node_manager.chain.validate_and_add_block(block):
                            self.log.info(
                                f"Block [{block_number_to_load + 1}/{info.blocks}] added {block.hash_block()} {datetime.datetime.now() - t}")
                            # if self.node_manager.chain.blocks_count() % 100 == 0:
                            #     self.log.info("Save chain")
                            #     self.node_manager.chain.save_chain_to_disk()
                        else:
                            self.log.info(f"{block_number_to_load + 1} reset")
                            self.node_manager.chain.drop_last_block()
                            # self.node_manager.chain.drop_last_block()
                    if info.blocks == self.node_manager.chain.blocks_count():
                        if info.latest_block != self.node_manager.chain.last_block_hash():
                            """ Цепи равны, но при этом разные блоки  """
                            drop_sync_signal = True
                            self.node_manager.chain.drop_last_block()

        if self._synced and drop_sync_signal and self.timer_drop_synced is not None:
            self.timer_drop_synced = time.time()
            self.log.info("Включен таймер потери синхронизации")

        if count_sync == 0 and not self._synced and time.time() > self.node_manager.start_time + Protocol.TIME_WAIN_CONNECT_TO_NODES_START:
            self.log.info("Ноды не найдены, включаем синхронизацию")
            self.set_node_synced(True)

        if count_sync > 0 and len(peer_info) > 1 and not drop_sync_signal and not self._synced:
            self.timer_drop_synced = None
            last_block_time = self.last_block_time()
            if self.node_manager.chain.time() > last_block_time + Protocol.BLOCK_START_CHECK_PAUSE and self.node_manager.chain.time() < last_block_time + Protocol.BLOCK_TIME_SECONDS / 2:
                self.log.info("Нода синхронизирована")
                self.set_node_synced(True)
                self.count_unsync_block = None
            else:
                self.log.info("Ждем начала блока")
                time.sleep(0.5)

        if self.is_synced():
            self.unsync_count = 0
            last_block_time = self.last_block_time()
            if self.node_manager.chain.time() > last_block_time + Protocol.BLOCK_START_CHECK_PAUSE:
                for address, info in peer_info.items():
                    if not self.is_valid_peer_info(info):
                        continue
                    if self.is_block_candidate_new(info):
                        self.node_manager.client_handler.request_block_candidate_from_peer(info.network_info)

            if self.unsync_count > 0:

                """ Требуется выяснить, текущая нода принадлежит главной цепи или нет """
                if self.node_manager.chain.time() > last_block_time + Protocol.BLOCK_TIME_SECONDS / 2:
                    print(""" в сети есть рассинхрон""", max_group, max_blocks, max_difficulty)

                flag_unsing = False
                if self.node_manager.chain.difficulty < max_difficulty:
                    if self.count_unsync_block is not None:
                        print("Сложность текущей цепи ниже чем в сети")
                    flag_unsing = True

                if self.node_manager.server.get_external_host_ip() not in max_group:
                    if self.count_unsync_block is not None:
                        print("Нода вне большинства")
                    flag_unsing = True

                if flag_unsing:
                    if self.count_unsync_block is None:
                        self.count_unsync_block = self.node_manager.chain.blocks_count()

                    print(
                        f"Нода в рассинхроне {self.node_manager.chain.blocks_count() - self.count_unsync_block} блоков")
                else:
                    self.count_unsync_block = None

                if self.count_unsync_block is not None and self.count_unsync_block + 1 < self.node_manager.chain.blocks_count():
                    print("Потеря синхронизации")
                    # снос последнего блока, для прокачки доминирующей цепи
                    self.node_manager.chain.drop_last_block()
                    self.set_node_synced(False)

    def last_block_time(self):
        return self.node_manager.chain.last_block_time()

    def is_valid_peer_info(self, info):
        if info is None:
            return False
        if not info.synced:
            return False
        if info.block_candidate == 'None':
            return False
        if info.blocks != self.node_manager.chain.blocks_count():
            # self.log.info("Различие в длине цепи", info.blocks, self.node_manager.chain.blocks_count())
            self.unsync_count += 1
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
                    self.check_sync(self.peer_info)

                    self.check_info_for_candidate(self.peer_info)

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
                    # self.node_manager.client_handler.servicer.ping_peers()

                    self.node_manager.client_handler.servicer.active_peers = self.node_manager.connect_manager.ping_peers()

                    self.node_manager.connect_manager.connect_to_peers()

                    self.node_manager.server.servicer.active_peers.update(
                        self.node_manager.connect_manager.active_peers)

                    # try:
                    #     self.node_manager.client_handler.connect_to_peers()
                    # except Exception as e:
                    #     self.log.error("error connect_to_peers", e)

                    if self.node_manager.enable_load_info:
                        self.peer_info = self.node_manager.client_handler.fetch_info_from_peers()

                if self.node_manager.chain.time() > self.last_block_time() + Protocol.BLOCK_START_CHECK_PAUSE and self.node_manager.chain.time() > self.last_block_time() + Protocol.BLOCK_START_CHECK_PAUSE + 1:
                    # как только сформировался блок, делаем опрос пиров
                    self.peer_info = self.node_manager.client_handler.fetch_info_from_peers()

                if self.is_synced() and timer_get_nodes + pause_ping < time.time():
                    timer_get_nodes = time.time()
                    self.node_manager.client_handler.get_peers_list()
                    self.node_manager.client_handler.fetch_transactions_from_all_peers()

                if not self.is_synced():
                    continue

                time.sleep(1)
            except KeyboardInterrupt:
                self.running = False
                exit()
            except Exception as e:
                self.log.error("Ошибка технического блока ", e)
                # self.running = False
