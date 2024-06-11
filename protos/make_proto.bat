
protoc -I/usr/local/include -I. \
  -I$GOPATH/src \
  -I$GOPATH/src/github.com/grpc-ecosystem/grpc-gateway/third_party/googleapis \
  --go_out=plugins=grpc:. \
  --grpc-gateway_out=logtostderr=true:. \
  network.proto

rem python -m grpc_tools.protoc -I. --python_out=. --grpc_python_out=. network.proto


