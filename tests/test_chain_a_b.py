from core.protocol import Protocol
from storage.chain import Chain
from core.Block import Block
from core.transaction import Transaction

def create_block(chain, address):
    last_block = chain.last_block()
    previousHash = None if last_block is None else last_block.hash_block()

    block = Block(previousHash)

    block.signer = address

    last_block_time = chain.last_block().timestamp_seconds if chain.last_block() is not None else chain.timestamp_seconds()

    # last_block_date = datetime.datetime.fromtimestamp(last_block_time)

    time_candidat = last_block_time + Protocol.block_interval()
    # синхронизированное время цепи
    block.timestamp_seconds = time_candidat if time_candidat > chain.time_ntpt.get_corrected_time() else chain.time_ntpt.get_corrected_time()

    # print(f"Create time: last_block_date{last_block_date}  candidat:{datetime.datetime.fromtimestamp(block.time)}")

    # is_key_block = self.protocol.is_key_block(block.previousHash)
    # print(f"Key block: {is_key_block}")

    # создание блока со своим адресом
    protocol = Protocol()
    seq_hash = protocol.sequence(block.previousHash)

    reward, ratio, lcs = protocol.reward(address, seq_hash)
    # print("seq_hash", seq_hash)

    tr = Transaction(tx_type="coinbase", fromAddress="0000000000000000000000000000000000",
                     toAddress=address, amount=reward)
    block.add_transaction(tr)

    block.hash_block()

    return block


adressA = "OutAQ43SUK6ZC2HRs5QozEnVqDaC68wtZTD2CocFXeX76Bi6ctsK"
# adressB = "OutAQ43SUK6ZC2HRs5QozEnVqDaC68wtZTD2CocFXeX76Bi6ctsK"
adressB = "OuteMMnVwafGWenuk9rehohCv5EB611VS4oJP2mLKrbEEPuRvcoU"


chainA = Chain()
chainB = Chain()
block_1_A = create_block(chainA, adressA)
block_1_B = create_block(chainB, adressB)
print(block_1_A.hash_block())
print(block_1_B.hash_block())

chainA.add_block_candidate(block_1_A)
chainB.add_block_candidate(block_1_B)

chainA.add_block_candidate(block_1_B)
chainB.add_block_candidate(block_1_A)



print(chainA.block_candidate.hash_block())
print(chainB.block_candidate.hash_block())
chainA.close_block()
chainB.close_block()
print("-----", chainA.last_block().signer)

block_2_A = create_block(chainA, adressA)
block_2_B = create_block(chainB, adressB)

chainA.add_block_candidate(block_2_A)
chainB.add_block_candidate(block_2_B)

chainA.add_block_candidate(block_2_B)
chainB.add_block_candidate(block_2_A)

print(chainA.block_candidate.hash_block())
print(chainB.block_candidate.hash_block())
chainA.close_block()
chainB.close_block()
print("-----", chainA.last_block().signer)


block_3_A = create_block(chainA, adressA)
block_3_B = create_block(chainB, adressB)

chainA.add_block_candidate(block_3_A)
chainB.add_block_candidate(block_3_B)

chainA.add_block_candidate(block_3_B)
chainB.add_block_candidate(block_3_A)

print(chainA.block_candidate.hash_block())
print(chainB.block_candidate.hash_block())
chainA.close_block()
chainB.close_block()
print("-----", chainA.last_block().signer)
