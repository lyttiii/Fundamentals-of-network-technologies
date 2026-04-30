import socket
import struct
import sys
import threading
import time

MESSAGE = b"Hello from your copy"
MULTICAST_TTL = 2
CHECK_INTERVAL = 5
stop_event = threading.Event()

if len(sys.argv) != 2:
    print("Usage: python main.py <multicast_group>")
    sys.exit(1)

multicast_group = sys.argv[1]
port = 10000

if ":" in multicast_group:
    family = socket.AF_INET6
else:
    family = socket.AF_INET

sockout = socket.socket(family, socket.SOCK_DGRAM, socket.IPPROTO_UDP)
sockout.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)

sockin = socket.socket(family, socket.SOCK_DGRAM, socket.IPPROTO_UDP)
sockin.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)

if family == socket.AF_INET:
    sockin.bind(('', port))
    sockout.bind(('', 0))
else:
    sockin.bind(('::', port))
    sockout.bind(('', 0))


ttl = MULTICAST_TTL
if family == socket.AF_INET:
    sockin.setsockopt(socket.IPPROTO_IP, socket.IP_MULTICAST_TTL, ttl)
else:
    sockin.setsockopt(socket.IPPROTO_IPV6, socket.IPV6_MULTICAST_HOPS, ttl)

def join_multicast_group(sockout, group):
    if family == socket.AF_INET:
        group_bin = socket.inet_aton(group)
        mreq = struct.pack("4sL", group_bin, socket.INADDR_ANY)
        sockout.setsockopt(socket.IPPROTO_IP, socket.IP_ADD_MEMBERSHIP, mreq)
    else:
        group_bin = socket.inet_pton(socket.AF_INET6, group)
        mreq = group_bin + struct.pack('@I', 0)
        sockout.setsockopt(socket.IPPROTO_IPV6, socket.IPV6_JOIN_GROUP, mreq)

join_multicast_group(sockin, multicast_group)

def send_messages():
    while not stop_event.is_set():
        try:
            print(f"\nSending message to group {multicast_group} on port {port}...")
            sockout.sendto(MESSAGE, (multicast_group, port))
            time.sleep(2)
        except Exception as e:
            print(f"Error sending message: {e}")
            break

def receive_messages():
    active_copies = {}
    sockin.settimeout(1)
    last_sent_time = 0

    while not stop_event.is_set():
        try:
            data, address = sockin.recvfrom(1024)
            print(address)
            if data == MESSAGE:
                ip_address = address
                current_time = time.time()
                active_copies[ip_address] = current_time + CHECK_INTERVAL
                active_copies = {ip: last_seen for ip, last_seen in active_copies.items() if current_time < last_seen}
                if current_time - last_sent_time >= 1:
                    print(f"Active copies: {list(active_copies.keys())}")
                    last_sent_time = current_time
        except socket.timeout:
            continue
        except Exception as e:
            print(f"Error receiving message: {e}")
            break

send_thread = threading.Thread(target=send_messages)
recv_thread = threading.Thread(target=receive_messages)

send_thread.start()
recv_thread.start()

try:
    while send_thread.is_alive() and recv_thread.is_alive():
        time.sleep(1)
except KeyboardInterrupt:
    print("\nStopping program...")

stop_event.set()
send_thread.join()
recv_thread.join()

try:
    sockin.close()
except Exception as e:
    print(f"Error closing socket: {e}")

print("Program terminated successfully.")
