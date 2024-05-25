import datetime
import hashlib
import time

from core.transaction import Transaction
from core.protocol import Protocol
import os, json
import random
from storage.transaction_storage import TransactionStorage, TransactionGenerator
import base64
# from crypto.xmss import *

class BlockHeader:
    def __init__(self):
        self.block_number = 0
        self.timestamp_seconds = 0
        self.previousHash = "0000000000000000000000000000000000000000000000000000000000000000"

