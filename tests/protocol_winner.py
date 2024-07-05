
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


# address_list = [
#     "RENHq1hm695mcctifs9qVbFDbkRkzryoqKpbE6jcCXv7aeruUwCo",
#     "SqCVtJsaTCRR2mJkotGPJB99F3afn3X3CMEaAg8QiPZ43vChnZ9u",
#     "R6mXsMvCTwbtyrL6gHVLYB1sVJv4hZacpYNWQ5w7JBYJwqVCPsSM",
#     "WasCYmasYuEuU5s3qUxWhwvAUKyAUasTuuap9BLSYWVn9ry2E4x1",
#     "BdbFzyqqZwbUFaFLnqmo97whqYnxPZ4RVZevDRJ33F7gN3WZJsMX",
#
#     "4iPEsZKhmX9rNYXJYnRdUYyRNidVaj2WFs4zLMZnbzmZfskJfYLr",
#     "2A1XVJgNT53C9c7JKUfHjbZtEQDk89fWd2cL3Ro3BNX2QG7crX2b",
#     "aJPVhagraL3uUwWyACkFzhHkPPDTGWyDJ7MUJKxQwfZqEkQXqvUW",
#
# ]
#
# previousHash = "f9b280306751658bfe3b4cf18baebea1bcec46ab2f5205a559f690249e4c4f4c"
#
# winner = protocol.winner(address_list, previousHash)
# print("List winner", winner)
#
# address_list = [
#
#     # "HT79Z8TaFqMe8PH1YHhYNxiYCrJEKUKykMVZ7LkXwebrLmcantbp",
#     # "SsuMDKa19x3fX3ZvaXMNjz8m7gqPiwfBzCFeQDJpVU9b6brK7bLE",
#     "Qggwc2mpEbrEKJN5umEPXNZxPo8CsbiwhpgfjMUJn4MAxg7PoyfE",
#     "bRiZZHstieg3BEYEPsTFzhMsm7CSj3x8TyFqeJj2x9UutTmGp2EB",
# ]
#
# winner = Protocol.winner(address_list, previousHash)
#
# print("List winner", winner)




def test_protocol_winner():
    address_list = [
        "RENHq1hm695mcctifs9qVbFDbkRkzryoqKpbE6jcCXv7aeruUwCo",
        "SqCVtJsaTCRR2mJkotGPJB99F3afn3X3CMEaAg8QiPZ43vChnZ9u",
        "R6mXsMvCTwbtyrL6gHVLYB1sVJv4hZacpYNWQ5w7JBYJwqVCPsSM",
        "WasCYmasYuEuU5s3qUxWhwvAUKyAUasTuuap9BLSYWVn9ry2E4x1",
        "BdbFzyqqZwbUFaFLnqmo97whqYnxPZ4RVZevDRJ33F7gN3WZJsMX",
        "4iPEsZKhmX9rNYXJYnRdUYyRNidVaj2WFs4zLMZnbzmZfskJfYLr",
        "2A1XVJgNT53C9c7JKUfHjbZtEQDk89fWd2cL3Ro3BNX2QG7crX2b",
        "aJPVhagraL3uUwWyACkFzhHkPPDTGWyDJ7MUJKxQwfZqEkQXqvUW",
    ]

    previousHash = "f9b280306751658bfe3b4cf18baebea1bcec46ab2f5205a559f690249e4c4f4c"

    group_size = 4
    groups = [address_list[i:i + group_size] for i in range(0, len(address_list), group_size)]

    winners = [Protocol.winner(group, previousHash) for group in groups]

    winner = Protocol.winner(winners, previousHash)
    print(winner)
    # Проверка, что все победители совпадают
    # assert all(winner == winners[0] for winner in winners), "Победители групп не совпадают!"
    #
    # print("Все тесты пройдены. Победитель:", winners[0])


test_protocol_winner()

