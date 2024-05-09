
from core.protocol import Protocol


protocol = Protocol()

a1 = "OutAQ43SUK6ZC2HRs5QozEnVqDaC68wtZTD2CocFXeX76Bi6ctsK"
a2 = "OuteMMnVwafGWenuk9rehohCv5EB611VS4oJP2mLKrbEEPuRvcoU"
previousHash = "0000000000000000000000000000000000000000000000000000000000000000"


win_address = protocol.winner(a1, a2, protocol.sequence(previousHash))
print("---------------------------------------------", protocol.sequence(previousHash))
print(a1)
print(a2)
print("win_address", win_address)

a2 = "OutAQ43SUK6ZC2HRs5QozEnVqDaC68wtZTD2CocFXeX76Bi6ctsK"
a1 = "OuteMMnVwafGWenuk9rehohCv5EB611VS4oJP2mLKrbEEPuRvcoU"
previousHash = "0000000000000000000000000000000000000000000000000000000000000000"


win_address = protocol.winner(a1, a2, protocol.sequence(previousHash))
print("---------------------------------------------", protocol.sequence(previousHash))
print(a1)
print(a2)
print("win_address", win_address)