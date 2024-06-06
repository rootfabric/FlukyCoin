# import protos.network_pb2 as network_pb2
#
# def test_field(version, synced, latest_block, block_candidate, uptime, peer_count, network_info, pending_transactions):
#     try:
#         response = network_pb2.PeerInfoResponse(
#             version=version,
#             synced=synced,
#             latest_block=latest_block,
#             block_candidate=block_candidate,
#             uptime=uptime,
#             peer_count=peer_count,
#             network_info=network_info,
#             pending_transactions=pending_transactions
#         )
#         print("PeerInfoResponse created successfully")
#         print(response)
#     except Exception as e:
#         print(f"Error occurred: {e}")
#
# def test_peer_info_response():
#     version = "0.1"
#     synced = False
#     latest_block = 9
#     block_candidate = "123"
#     uptime = "8.827643632888794"
#     peer_count = 2
#     network_info = "192.168.0.26:9334"
#     pending_transactions = 0
#
#     # Test each field one by one
#     print("Testing version")
#     test_field(version, True, 0, "", "", 0, "", 0)
#     print("Testing synced")
#     test_field("", synced, 0, "", "", 0, "", 0)
#     print("Testing latest_block")
#     test_field("", True, latest_block, "", "", 0, "", 0)
#     print("Testing block_candidate")
#     test_field("", True, 0, block_candidate, "", 0, "", 0)
#     print("Testing uptime")
#     test_field("", True, 0, "", uptime, 0, "", 0)
#     print("Testing peer_count")
#     test_field("", True, 0, "", "", peer_count, "", 0)
#     print("Testing network_info")
#     test_field("", True, 0, "", "", 0, network_info, 0)
#     print("Testing pending_transactions")
#     test_field("", True, 0, "", "", 0, "", pending_transactions)
#
# test_peer_info_response()


import protos.network_pb2

def test_peer_info_response():
    try:
        response = protos.network_pb2.PeerInfoResponse(
            version="0.1",
            synced=False,
            latest_block="9",
            block_candidate="123",
            uptime="8.827643632888794",
            peer_count=2,
            network_info="192.168.0.26:9334",
            pending_transactions=0
        )
        print("PeerInfoResponse created successfully")
        print(response)
    except Exception as e:
        print(f"Error occurred: {e}")

test_peer_info_response()
