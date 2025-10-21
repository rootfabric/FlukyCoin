import json
import os
import sqlite3
import threading
from typing import Dict, Iterable, List, Optional


class StakeRegistry:
    """Хранилище стейков валидаторов с учётом истории блоков."""

    def __init__(self, dir: str):
        self.dir = dir
        self.local = threading.local()
        self._init_db()

    # --- база данных -----------------------------------------------------
    def _init_db(self) -> None:
        dir_name = self.dir.replace(":", "_")
        base_dir = "node_data"
        dir_path = os.path.join(base_dir, dir_name)
        if not os.path.exists(dir_path):
            os.makedirs(dir_path)
        self.db_path = os.path.join(dir_path, "stakes.db")

    def _get_conn(self) -> sqlite3.Connection:
        if not hasattr(self.local, "conn"):
            self.local.conn = sqlite3.connect(self.db_path)
            self._create_tables(self.local.conn)
        return self.local.conn

    @staticmethod
    def _create_tables(conn: sqlite3.Connection) -> None:
        with conn:
            conn.execute(
                """
                CREATE TABLE IF NOT EXISTS validators (
                    address TEXT PRIMARY KEY,
                    stake INTEGER NOT NULL,
                    public_key TEXT
                )
                """
            )
            conn.execute(
                """
                CREATE TABLE IF NOT EXISTS stake_history (
                    block_number INTEGER NOT NULL,
                    address TEXT NOT NULL,
                    delta INTEGER NOT NULL,
                    meta TEXT,
                    PRIMARY KEY (block_number, address)
                )
                """
            )

    # --- чтение ----------------------------------------------------------
    def all_validators(self) -> List[Dict[str, Optional[str]]]:
        with self._get_conn() as conn:
            cursor = conn.execute(
                "SELECT address, stake, public_key FROM validators ORDER BY address"
            )
            return [
                {
                    "address": row[0],
                    "stake": int(row[1]),
                    **({"public_key": row[2]} if row[2] is not None else {}),
                }
                for row in cursor
            ]

    def get_stake(self, address: str) -> int:
        with self._get_conn() as conn:
            cursor = conn.execute(
                "SELECT stake FROM validators WHERE address=?", (address,)
            )
            row = cursor.fetchone()
        return int(row[0]) if row else 0

    def total_stake(self) -> int:
        with self._get_conn() as conn:
            cursor = conn.execute("SELECT SUM(stake) FROM validators")
            row = cursor.fetchone()
        return int(row[0]) if row and row[0] is not None else 0

    # --- инициализация ----------------------------------------------------
    def initialize_from_genesis(self, validators: Iterable[Dict[str, int]], block_number: int) -> None:
        validators = list(validators or [])
        if not validators:
            return

        with self._get_conn() as conn:
            cursor = conn.execute("SELECT COUNT(*) FROM validators")
            if cursor.fetchone()[0] > 0:
                return

            with conn:
                for entry in validators:
                    address = entry["address"]
                    stake = int(entry.get("stake", 0))
                    public_key = entry.get("public_key")
                    conn.execute(
                        "INSERT INTO validators (address, stake, public_key) VALUES (?, ?, ?)",
                        (address, stake, public_key),
                    )
                    conn.execute(
                        "INSERT OR REPLACE INTO stake_history (block_number, address, delta, meta) VALUES (?, ?, ?, ?)",
                        (
                            block_number,
                            address,
                            stake,
                            json.dumps({"type": "genesis"}),
                        ),
                    )

    # --- обновление состояния --------------------------------------------
    def apply_block(self, block) -> None:
        validators = getattr(block, "validators", [])
        if block.block_number == 0:
            self.initialize_from_genesis(validators, block.block_number)

        deltas: Dict[str, int] = {}

        for transaction in block.transactions:
            if transaction.tx_type != "coinbase":
                continue
            for index, address in enumerate(transaction.toAddress):
                amount = int(transaction.amounts[index])
                deltas[address] = deltas.get(address, 0) + amount

        if not deltas:
            return

        with self._get_conn() as conn:
            with conn:
                for address, delta in deltas.items():
                    cursor = conn.execute(
                        "SELECT stake, public_key FROM validators WHERE address=?",
                        (address,),
                    )
                    row = cursor.fetchone()
                    current = int(row[0]) if row else 0
                    public_key = row[1] if row else None

                    new_value = max(0, current + delta)

                    if row is None:
                        conn.execute(
                            "INSERT INTO validators (address, stake, public_key) VALUES (?, ?, ?)",
                            (address, new_value, public_key),
                        )
                    else:
                        conn.execute(
                            "UPDATE validators SET stake=? WHERE address=?",
                            (new_value, address),
                        )

                    conn.execute(
                        "INSERT OR REPLACE INTO stake_history (block_number, address, delta, meta) VALUES (?, ?, ?, ?)",
                        (
                            block.block_number,
                            address,
                            delta,
                            json.dumps({"type": "reward"}),
                        ),
                    )

    def rollback_block(self, block) -> None:
        with self._get_conn() as conn:
            cursor = conn.execute(
                "SELECT address, delta FROM stake_history WHERE block_number=?",
                (block.block_number,),
            )
            history = cursor.fetchall()

        if not history:
            return

        with self._get_conn() as conn:
            with conn:
                for address, delta in history:
                    cursor = conn.execute(
                        "SELECT stake FROM validators WHERE address=?",
                        (address,),
                    )
                    row = cursor.fetchone()
                    current = int(row[0]) if row else 0
                    new_value = current - int(delta)
                    if new_value <= 0:
                        conn.execute(
                            "DELETE FROM validators WHERE address=?",
                            (address,),
                        )
                    else:
                        conn.execute(
                            "UPDATE validators SET stake=? WHERE address=?",
                            (new_value, address),
                        )

                conn.execute(
                    "DELETE FROM stake_history WHERE block_number=?",
                    (block.block_number,),
                )

    def clear(self) -> None:
        with self._get_conn() as conn:
            with conn:
                conn.execute("DELETE FROM validators")
                conn.execute("DELETE FROM stake_history")

