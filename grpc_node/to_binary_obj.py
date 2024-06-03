import datetime
import network_pb2
import network_pb2_grpc

# Функция для создания объекта NodeInfoResponse и его сериализации
def create_serialized_node_info(version, state):
    node_info = network_pb2.NodeInfoResponse()
    node_info.version = version
    node_info.state = state
    node_info.current_time = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")

    # Сериализация данных в бинарный формат
    serialized_data = node_info.SerializeToString()
    return serialized_data


# Функция для десериализации данных обратно в объект NodeInfoResponse
def parse_serialized_node_info(serialized_data):
    node_info = network_pb2.NodeInfoResponse()
    node_info.ParseFromString(serialized_data)
    return node_info


# Пример использования
serialized_node_info = create_serialized_node_info("1.0", "active")
retrieved_node_info = parse_serialized_node_info(serialized_node_info)

print("Version:", retrieved_node_info.version)
print("State:", retrieved_node_info.state)
print("Current Time:", retrieved_node_info.current_time)
