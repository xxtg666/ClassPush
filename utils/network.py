import socket
import logging

logger = logging.getLogger("classpush.network")


def get_local_ips() -> list:
    ips = []
    try:
        hostname = socket.gethostname()
        for info in socket.getaddrinfo(hostname, None):
            ip = info[4][0]
            if ":" not in ip and (
                ip.startswith("192.168.")
                or ip.startswith("10.")
                or ip.startswith("172.")
            ):
                if ip not in ips:
                    ips.append(ip)
    except Exception as e:
        logger.warning("Failed to get local IPs: %s", e)
    return ips


def find_available_port(start_port=8080, max_tries=10) -> int:
    for port in range(start_port, start_port + max_tries):
        try:
            sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            sock.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
            sock.bind(("0.0.0.0", port))
            sock.close()
            return port
        except OSError:
            continue
    raise RuntimeError(
        f"No available port found in range {start_port}-{start_port + max_tries}"
    )


def get_primary_ip() -> str:
    try:
        s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        s.connect(("8.8.8.8", 80))
        ip = s.getsockname()[0]
        s.close()
        return ip
    except Exception:
        ips = get_local_ips()
        return ips[0] if ips else "127.0.0.1"
