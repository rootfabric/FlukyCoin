
from core.protocol import Protocol


protocol = Protocol()

# # a1 = "OutAQ43SUK6ZC2HRs5QozEnVqDaC68wtZTD2CocFXeX76Bi6ctsK"
# # a2 = "OuteMMnVwafGWenuk9rehohCv5EB611VS4oJP2mLKrbEEPuRvcoU"
# # previousHash = "0000000000000000000000000000000000000000000000000000000000000000"
#

#
# a1 = "OutGkzTP3mv8x7t3zwUM3Ly8YfhEY79oNdpBRgtobK2fDSFH_OFF"
# a2 = "OuteMMnVwafGWenuk9rehohCv5EB611VS4oJP2mLKrbEEPuRSERV1"
# a3 = "OuteMMnVwafGWenuk9rehohCv5EB611VS4oJP2mLKrbEEPuRvcVS"
#
# win_address = protocol.winner(a1, a2, protocol.sequence(previousHash))
# print("-----", protocol.sequence(previousHash))
# print(a1)
# print(a2)
# print("win_address", win_address)
#
# # a2 = "OutAQ43SUK6ZC2HRs5QozEnVqDaC68wtZTD2CocFXeX76Bi6ctsK"
# # a1 = "OuteMMnVwafGWenuk9rehohCv5EB611VS4oJP2mLKrbEEPuRvcoU"
# # previousHash = "0000000000000000000000000000000000000000000000000000000000000000"
#
#
# win_address = protocol.winner(a2, a3, protocol.sequence(previousHash))
# print("---------------------------------------------", protocol.sequence(previousHash))
# print(a1)
# print(a2)
# print("win_address", win_address)


address_list = [
    "bRiZZHstieg3BEYEPsTFzhMsm7CSj3x8TyFqeJj2x9UutTmGp2EB",
    "HT79Z8TaFqMe8PH1YHhYNxiYCrJEKUKykMVZ7LkXwebrLmcantbp",
    "SsuMDKa19x3fX3ZvaXMNjz8m7gqPiwfBzCFeQDJpVU9b6brK7bLE",
    "Qggwc2mpEbrEKJN5umEPXNZxPo8CsbiwhpgfjMUJn4MAxg7PoyfE",

]

previousHash = "f9b280306751658bfe3b4cf18baebea1bcec46ab2f5205a559f690249e4c4f4c"

winner = protocol.winner(address_list, previousHash)
print("List winner", winner)

address_list = [

    # "HT79Z8TaFqMe8PH1YHhYNxiYCrJEKUKykMVZ7LkXwebrLmcantbp",
    # "SsuMDKa19x3fX3ZvaXMNjz8m7gqPiwfBzCFeQDJpVU9b6brK7bLE",
    "Qggwc2mpEbrEKJN5umEPXNZxPo8CsbiwhpgfjMUJn4MAxg7PoyfE",
    "bRiZZHstieg3BEYEPsTFzhMsm7CSj3x8TyFqeJj2x9UutTmGp2EB",
]

winner = Protocol.winner(address_list, previousHash)

print("List winner", winner)


