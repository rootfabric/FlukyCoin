
import socket
import ipaddress

def validate_and_resolve_address_with_port(address):
    try:
        # Разделение адреса и порта
        ip_port_split = address.split(':')
        if len(ip_port_split) != 2:
            print("Адрес должен содержать порт, разделённый двоеточием", address)
            return None

        ip_or_domain, port = ip_port_split[0], ip_port_split[1]

        # Проверка валидности порта
        if not (0 <= int(port) <= 65535):
            print("Некорректный порт", address)
            return None

        # Проверка и разрешение IP-адреса или доменного имени
        ip = ipaddress.ip_address(ip_or_domain)
        return f"{ip}:{port}"  # Возвращаем IP-адрес с портом, если он валиден
    except ValueError:
        # Если адрес не является валидным IP, проверяем, является ли он доменным именем
        try:
            ip = socket.gethostbyname(ip_or_domain)
            return f"{ip}:{port}"  # Возвращаем IP, полученный из доменного имени с портом
        except socket.gaierror:
            print("Адрес не найден или некорректен", address)  # Ошибка разрешения доменного имени
            return None

def check_port_open(address):
    # Разделение адреса и порта
    ip_port_split = address.split(':')
    if len(ip_port_split) != 2:
        print("Адрес должен содержать порт, разделённый двоеточием", address)
        return None

    ip_or_domain, port = ip_port_split[0], int(ip_port_split[1])

    # Проверка валидности порта
    if not (0 <= port <= 65535):
        print("Некорректный порт", address)
        return None

    sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    sock.settimeout(5)  # Установка тайм-аута в 5 секунд

    try:
        # Попытка соединения с адресом и портом
        result = sock.connect_ex((ip_or_domain, port))
        if result == 0:
            return True  # Порт открыт
        else:
            return False  # Порт закрыт
    except socket.error as e:
        return False  # В случае ошибки соединения считаем порт закрытым
    finally:
        sock.close()  # Закрываем сокет


from ipwhois import IPWhois
import ipaddress

def is_private_ip(ip):
    private_ip_ranges = [
        ipaddress.ip_network('10.0.0.0/8'),
        ipaddress.ip_network('172.16.0.0/12'),
        ipaddress.ip_network('192.168.0.0/16')
    ]
    ip_obj = ipaddress.ip_address(ip)
    return any(ip_obj in net for net in private_ip_ranges)

def get_ip_info(ip):
    obj = IPWhois(ip)
    res = obj.lookup_rdap()
    return res


def check_ip(ip_or_domain):
    try:
        ip = socket.gethostbyname(ip_or_domain)
    except socket.gaierror:
        return f'Не удалось разрешить домен: {ip_or_domain}'

    if is_private_ip(ip):
        return f'IP-адрес {ip} ({ip_or_domain}) является частным и не виден в интернете.'
    else:
        ip_info = get_ip_info(ip)
        if ip_info['asn'] is None:
            return f'IP-адрес {ip} ({ip_or_domain}) не является публичным и не виден в интернете.'
        else:
            return f'IP-адрес {ip} ({ip_or_domain}) является публичным и виден в интернете.'


if __name__ == '__main__':
    # Примеры использования функции
    # print(validate_and_resolve_address_with_port("5.35.98.126:9333"))  # Выведет: 192.168.1.1
    #
    # print(check_port_open("google.com:80"))
    # print(check_port_open("5.35.98.126:9333"))
    # print(check_port_open("192.168.0.26:9334"))

    # ip = '8.8.8.8'
    # ip = '5.35.98.126'
    ip = 'glamazdin.fvds.ru'
    ip = 'ya.ru'
    ip = '192.168.0.26'
    print(check_ip(ip))
