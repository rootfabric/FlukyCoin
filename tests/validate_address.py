from crypto.xmss import XMSSPublicKey


print(XMSSPublicKey().is_valid_address('ZLbCBjiYF3LYK7L8pjDzquWxfu1zuwbP3mvsUhfihoxYGhGFtXgp'))

info = XMSSPublicKey().address_info('ZLbCBjiYF3LYK7L8pjDzquWxfu1zuwbP3mvsUhfihoxYGhGFtXgp')
print(info)

address_height = XMSSPublicKey().address_height('ZLbCBjiYF3LYK7L8pjDzquWxfu1zuwbP3mvsUhfihoxYGhGFtXgp')
print("address_height", address_height)

address_max_sign = XMSSPublicKey().address_max_sign('ZLbCBjiYF3LYK7L8pjDzquWxfu1zuwbP3mvsUhfihoxYGhGFtXgp')
print("address_max_sign", address_max_sign)


