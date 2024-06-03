#python -m grpc_tools.protoc -I. --python_out=. --grpc_python_out=. network.proto
python -m grpc_tools.protoc -I./protos --python_out=. --grpc_python_out=. ./protos/network.proto

