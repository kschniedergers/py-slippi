from typing import Callable, Dict, Union
from base64 import b64decode
from pyee import
import json
import enet
import io

# maybe not needed
import socket

from slippi.util import Base, IntEnum

from .parse import parse_event

DEFAULT_IP = '0.0.0.0'
DEFAULT_PORT = 51441
INITIAL_CONNECT_TIMEOUT = 1000  # ms
HANDSHAKE_TIMEOUT = 1000  # ms
SERVICE_LOOP_TIMEOUT = 10000  # ms


class ConnectionStatus(IntEnum):
    """Status of the connection to dolphin"""
    DISCONNECTED = 0
    CONNECTING = 1
    CONNECTED = 2
    RECONNECT_WAIT = 3


class ConnectionEvent:
    CONNECT = "connect"
    MESSAGE = "message"
    HANDSHAKE = "handshake"
    STATUS_CHANGE = "statusChange"
    DATA = "data"
    ERROR = "error"

    GAME_START = 'game_start'
    GAME_END = 'game_end'


class DolphinMessageType:
    CONNECT_REPLY = "connect_reply"
    GAME_EVENT = "game_event"
    START_GAME = "start_game"
    END_GAME = "end_game"


class DolphinConnection(Base):

    ip_address: str
    port: int
    connection_status: ConnectionStatus
    game_cursor: int
    nickname: str
    version: str
    handlers: Dict[ConnectionEvent, Callable[..., None]]
    # do i need union?
    peer: Union[enet.Peer, None]
    test: any
    lazy: any = []
    lazy2: any = []

    def __init__(self, handlers: Dict[ConnectionEvent, Callable[..., None]], ip: str = DEFAULT_IP, port: int = DEFAULT_PORT):
        self.ip_address = ip
        self.port = port
        self.handlers = handlers

    # look into skip frames and if it should be added
    # look into cursor start
    def connect(self):

        ip_bytes = socket.inet_aton(self.ip_address)

        # todo configurable numbers
        self.host = enet.Host(None, 10, 0, 0)
        self.host.connect(enet.Address(ip_bytes, self.port), 10, 1337)

        # todo detect errors and probably print something
        first_connect = self.host.service(INITIAL_CONNECT_TIMEOUT)
        if (first_connect.type != enet.EVENT_TYPE_CONNECT):
            print('something went wrong while connecting!')
            return

        self._send_handler_event(ConnectionEvent.CONNECT, first_connect)

        self.peer = first_connect.peer

        HANDSHAKE = {
            "type": "connect_request",
            "cursor": 0,
        }
        packet = enet.Packet(str.encode(json.dumps(HANDSHAKE)))
        self.peer.send(0, packet)

        loopamt = 0
        while True:
            response = self.host.service(SERVICE_LOOP_TIMEOUT)

            if response.type == enet.EVENT_TYPE_NONE:
                continue
                # probably do a cooldown or summin

            self._send_handler_event(ConnectionEvent.MESSAGE, response)

            if response.type == enet.EVENT_TYPE_DISCONNECT:
                pass
                # disconnect stuff
            elif response.type == enet.EVENT_TYPE_RECEIVE:
                data = json.loads(response.packet.data)

                if data['type'] == DolphinMessageType.CONNECT_REPLY:
                    handshake_response_packet = json.loads(
                        response.packet.data
                    )

                    self.connection_status = ConnectionStatus.CONNECTED
                    self.game_cursor = handshake_response_packet.get('cursor')
                    self.nickname = handshake_response_packet.get('nick')
                    self.version = handshake_response_packet.get('version')

                    self._send_handler_event(
                        ConnectionEvent.HANDSHAKE, response
                    )
                    # self.test = response
                    continue

                self._send_handler_event(ConnectionEvent.DATA)

            else:
                # idk
                pass

            self.lazy2.append(response)
            loopamt += 1
            if loopamt > 1000:
                return

    def _send_handler_event(self, event: ConnectionEvent, param: any):
        handler = self.handlers.get(event)
        if handler:
            handler(param)

    # CONNECT = "connect"
    # MESSAGE = "message"
    # HANDSHAKE = "handshake"
    # STATUS_CHANGE = "statusChange"
    # DATA = "data"
    # ERROR = "error"


# ########
# import enet
# import socket
# import json
# import time

# ipb = socket.inet_aton('0.0.0.0')

# HANDSHAKE = {
#     "type": "connect_request",
#     "cursor": 0,
# }

# packet = enet.Packet(str.encode(json.dumps(HANDSHAKE)))

# host = enet.Host(None, 10, 0, 0)
# peer = host.connect(enet.Address(ipb, 51441), 10, 1337)

# HANDSHAKE = {
#     "type": "connect_request",
#     "cursor": 0,
# }
# packet = enet.Packet(str.encode(json.dumps(HANDSHAKE)))

# first = host.service(1000)
# peer = first.peer

# a = peer.send(0, packet)

# # f = host.service(10000)

# # print(f.packet.data)

# last = None

# while True:
#     packet = host.service(5000)
#     if packet.type == enet.EVENT_TYPE_DISCONNECT:
#         print('disconect event gotten')
#         break
#     elif packet.type != enet.EVENT_TYPE_NONE:
#         last = packet
#         print(packet.packet.data)
#     else:
#         print('lets go round one more time')

# "OQcBAAH//w=="
# b'{"cursor":50625,"next_cursor":50626,"payload":"OQcBAAH//w==","type":"game_event"}'
# b'{"cursor":50624,"next_cursor":50625,"payload":"OgAAKt4rWZw6AAArWTcAACreAAArWZw6AP3Cn3KxwbizDz+AAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAEJ+4Ug3AAAq3gEAK1mcOgFnwvLnzcLTvOk/gAAAAAAAAAAAAAAAAAAAAAAAAD+AAACAAAAAAAA9g6g7P4AAAABC5OFIOAAAKt4AAAIA/cKfcrHBuLMPP4AAAEJ+4UhCcAAAEAEGAUBAAABEAAAAAAAAAAMBAAMBAAIAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAADZOAAAKt4BAAIBZ8LwdGLC2192P4AAAELk4UhCcAAADQEAAUGoAADEAAAAgAAAABQBAAMAAAA/nNqswHRRmAAAAAAAAAAAAAAAAAAAAAAAAAE5PAAAKt4AACre","type":"game_event"}'
