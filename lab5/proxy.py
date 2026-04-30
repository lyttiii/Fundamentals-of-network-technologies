import asyncio
import sys
import logging
import socket
import dns.resolver

COMMAND_CONNECT = 0x01
ADDRESS_TYPE_DOMAIN = 0x03
BUFFER_SIZE = 4096


async def start_server(host, port):
    logging.info(f"Proxy server started at {host}:{port}")
    server = await asyncio.start_server(handle_connection, host, port)
    while True:
        await asyncio.sleep(5)


async def handle_connection(reader: asyncio.StreamReader, writer: asyncio.StreamWriter):
    client_info = writer.get_extra_info('peername')
    logging.info(f"{client_info}: connected")

    if not await authenticate_client(reader, writer):
        writer.write_eof() # больше данных клиенту не отправляем
        await writer.drain()
        writer.close()
        await writer.wait_closed()
        return

    host, port = await handle_client_request(reader, writer)
    if host is None or port is None:
        writer.close()
        await writer.wait_closed()
        return

    try:
        remote_reader, remote_writer = await asyncio.open_connection(host, port)
    except ConnectionRefusedError:
        logging.info(f"{client_info}: connection refused to {host}:{port}")
        writer.write(b'\x05\x05\x00\x01\x00\x00\x00\x00\x00\x00')
        writer.write_eof()
        await writer.drain()
        writer.close()
        await writer.wait_closed()
        return
    except TimeoutError:
        logging.info(f"{client_info}: unreachable host: {host}:{port}")
        writer.write(b'\x05\x04\x00\x01\x00\x00\x00\x00\x00\x00')
        writer.write_eof()
        await writer.drain()
        writer.close()
        await writer.wait_closed()
        return
    except Exception as e:
        logging.info(f"{client_info}: error while connecting to {host}:{port} - {e}")
        writer.write(b'\x05\x01\x00\x01\x00\x00\x00\x00\x00\x00')
        writer.write_eof()
        await writer.drain()
        writer.close()
        await writer.wait_closed()
        return

    logging.info(f"{client_info}: connected successfully to {host}:{port}")
    local_host, local_port = remote_writer.get_extra_info('sockname')
    writer.write(b'\x05\x00\x00\x01' + socket.inet_aton(local_host) + local_port.to_bytes(2, 'big')) # отправляем клиенту что успешно соеденились с сервером
    try:
        await asyncio.gather(
            transfer_data(reader, remote_writer),
            transfer_data(remote_reader, writer)
        )
    except Exception as e:
        logging.info(f"{client_info}: error while forwarding to {host}:{port} - {e}")
    finally:
        logging.info(f"{client_info}: connection closed to {host}:{port}")
        writer.close()
        remote_writer.close()


async def authenticate_client(reader, writer) -> bool:
    client_info = writer.get_extra_info('peername')
    version = int((await reader.readexactly(1))[0])
    if version != 0x05:
        logging.info(f"{client_info}: connection refused")
        return False

    num_methods = int((await reader.readexactly(1))[0])
    methods = await reader.readexactly(num_methods)
    if 0x00 not in methods:
        logging.info(f"{client_info}: no acceptable methods")
        writer.write(bytes([0x05, 0xff]))
        await writer.drain()
        return False

    writer.write(bytes([0x05, 0x00]))
    await writer.drain()
    return True


async def handle_client_request(reader: asyncio.StreamReader, writer: asyncio.StreamWriter) -> tuple:
    client_info = writer.get_extra_info('peername')
    version = int((await reader.readexactly(1))[0])
    if version != 0x05:
        logging.info(f"{client_info}: connection refused")
        return None

    command = int((await reader.readexactly(1))[0])
    if command != COMMAND_CONNECT:
        logging.info(f"{client_info}: unsupported command")
        writer.write(b'\x05\x07\x00\x01\x00\x00\x00\x00\x00\x00')
        await writer.drain()
        return None

    await reader.readexactly(1)  # резервный байт 0x00
    address_type = int((await reader.readexactly(1))[0])
    domain_name = None
    if address_type == 0x01:  # IPv4
        host = socket.inet_ntoa(await reader.readexactly(4))
    elif address_type == ADDRESS_TYPE_DOMAIN:
        domain_length = int((await reader.readexactly(1))[0])
        domain_name = (await reader.readexactly(domain_length)).decode()
        try:
            host = dns.resolver.resolve(domain_name, 'A')[0].to_text()
        except (dns.resolver.NoAnswer, dns.resolver.NXDOMAIN) as e:
            logging.error(f"{client_info}: DNS resolution failed for {domain_name} - {e}")
            try:
                host = socket.gethostbyname(domain_name)
            except socket.gaierror as e:
                logging.error(f"{client_info}: Fallback DNS resolution failed for {domain_name} - {e}")
                writer.write(b'\x05\x04\x00\x01\x00\x00\x00\x00\x00\x00')
                await writer.drain()
                return None, None
    else:
        writer.write(b'\x05\x08\x00\x01\x00\x00\x00\x00\x00\x00')
        await writer.drain()
        return None, None

    port = int.from_bytes(await reader.readexactly(2), 'big')

    if domain_name:
        logging.info(f"{client_info}: host: {host} ({domain_name})")
    else:
        logging.info(f"{client_info}: host: {host}")

    logging.info(f"{client_info}: port: {port}")

    return host, port


async def transfer_data(reader: asyncio.StreamReader, writer: asyncio.StreamWriter):
    while not reader.at_eof():
        data = await reader.read(BUFFER_SIZE)
        writer.write(data)
        await writer.drain()
    writer.write_eof()
    await writer.drain()


if __name__ == "__main__":
    logging.getLogger().name = 'proxy'
    logging.getLogger().setLevel(logging.INFO)
    if len(sys.argv) < 2:
        print(f"usage: python proxy.py <port>")
    else:
        event_loop = asyncio.new_event_loop()
        asyncio.set_event_loop(event_loop)
        event_loop.run_until_complete(start_server('', int(sys.argv[1])))
        event_loop.close()