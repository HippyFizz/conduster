import socket
import struct

from ipwhois import IPWhois


def ip2int(addr):
    """
    :param addr: '127.0.0.1'
    :type addr: str
    :return:
    :rtype: int
    """
    return struct.unpack("!I", socket.inet_aton(addr))[0]


def int2ip(addr):
    """
    :param addr:
    :type addr: int
    :return: '127.0.0.1'
    :rtype: str
    """
    return socket.inet_ntoa(struct.pack("!I", addr))

def ip_int2subnet_int(ip_int):
    """
    just set last octet of ip to 0
    :param ip_int:
    :type ip_int: int
    :return:
    :rtype: int
    """
    return ip_int >> 8 << 8

def ip_int2subnet(ip_int):
    """
    just set last octet of ip to 0
    :param ip_int:
    :type ip_int: int
    :return: '127.0.0.0'
    :rtype: str
    """
    subnet_int = ip_int2subnet_int(ip_int)
    return int2ip(subnet_int)


def ip2subnet(addr):
    """
    :param addr: '127.0.0.1'
    :type addr: str
    :return: '127.0.0.0'
    :rtype: str
    """
    ip_int = ip2int(addr)
    return ip_int2subnet(ip_int)

def ip_provider(ip):
    """
    :param ip: '77.159.16.10'
    :type ip: str
    :return: provider name
    :rtype: str
    """
    if not ip:
        return None
    try:
        return IPWhois(ip).lookup_rdap()
    except:
        return None