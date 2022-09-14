from typing import Callable, Dict, Union
from base64 import b64decode
import json
import enet
import io

# maybe not needed
import socket

from slippi.util import Base, IntEnum

from .parse import parse_event

DEFAULT_IP = '0.0.0.0'
DEFAULT_PORT = 51441
INITIAL_CONNECT_TIMEOUT = 1000 # ms
HANDSHAKE_TIMEOUT = 1000 # ms
SERVICE_LOOP_TIMEOUT = 10000 # ms

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

class DolphinMessageType:
    CONNECT_REPLY = "connect_reply"
    GAME_EVENT = "game_event"
    START_GAME = "start_game"
    END_GAME = "end_game"

class DolphinConnection(Base):

    ipAddress: str
    port: int
    connectionStatus: ConnectionStatus
    gameCursor: int
    nickname: str
    version: str
    # do i need union?
    peer: Union[enet.Peer, None]
    test: any
    lazy: any = []

    def __init__(self, ip: str = DEFAULT_IP, port: int = DEFAULT_PORT):
        self.ipAddress = ip
        self.port = port

    # look into skip frames and if it should be added
    # look into cursor start
    def connect(self, handlers: Dict[ConnectionEvent, Callable[..., None]]):

        ipBytes = socket.inet_aton(self.ipAddress)

        # todo configurable numbers
        self.host = enet.Host(None, 10, 0, 0)
        self.host.connect(enet.Address(ipBytes, self.port), 10, 1337)

        # todo detect errors and probably print something
        firstConnect = self.host.service(INITIAL_CONNECT_TIMEOUT)
        if (firstConnect.type != enet.EVENT_TYPE_CONNECT):
            print('something went wrong while connecting!')
            return

        self.peer = firstConnect.peer


        HANDSHAKE = {
            "type": "connect_request",
            "cursor": 0,
        }
        packet = enet.Packet(str.encode(json.dumps(HANDSHAKE)))
        self.peer.send(0, packet)

        handshakeResponse = self.host.service(HANDSHAKE_TIMEOUT)

        if handshakeResponse.type == enet.EVENT_TYPE_RECEIVE:
            handshakeResponsePacket = json.loads(handshakeResponse.packet.data)
            assert(handshakeResponsePacket['type'] == DolphinMessageType.CONNECT_REPLY)
            
            self.connectionStatus = ConnectionStatus.CONNECTED
            self.gameCursor = handshakeResponsePacket.get('cursor')
            self.nickname = handshakeResponsePacket.get('nick')
            self.version = handshakeResponsePacket.get('version')
            
            handler = handlers.get(ConnectionEvent.CONNECT)
            if handler:
                handler(handshakeResponse)
            self.test = handshakeResponse
        elif handshakeResponse.type == enet.EVENT_TYPE_NONE:
            print("handshake timed out!")
        else:
            self.test = handshakeResponse


        loopamt = 0
        while True:
            response = self.host.service(SERVICE_LOOP_TIMEOUT)

            if response.type == enet.EVENT_TYPE_NONE:
                pass
                #probably do a cooldown or summin
            elif response.type == enet.EVENT_TYPE_DISCONNECT:
                pass
                # disconnect stuff
            elif response.type == enet.EVENT_TYPE_RECEIVE:
                data = json.loads(response.packet.data)
                if data['type'] == DolphinMessageType.START_GAME:
                    pass
                    # start
                elif data['type'] == DolphinMessageType.GAME_EVENT:
                    bytes = io.BytesIO(b64decode(data['packet']['data']))
                    event = parse_event(bytes)
                    # frame
                elif data['type'] == DolphinMessageType.END_GAME:
                    pass

            else:
                # idk
                pass

            


            self.lazy.append(response)
            loopamt += 1
            if loopamt > 1000:
                return



            

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