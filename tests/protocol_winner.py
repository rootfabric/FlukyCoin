
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
    "OuteMMnVwafGWenuk9rehohCv5EB611VS4oJP2mLKrbEEPuRvcVS",
    "OutGkzTP3mv8x7t3zwUM3Ly8YfhEY79oNdpBRgtobK2fDSFH_OFF",
    "OuteMMnVwafGWenuk9rehohCv5EB611VS4oJP2mLKrbEEPuRSERV1",

]
previousHash = "c8f11d0dea353cb425932508758fc531304eb76ece2afceca94cbf71769ffe8a"
winner = address_list[0]
for i, address in enumerate(address_list[:-1]):
    winner = protocol.winner(winner, address_list[i+1], protocol.sequence(previousHash))
    print(winner)

print("List winner", winner)


