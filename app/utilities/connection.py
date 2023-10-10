import re
import uuid
import time
import socket
import random
import requests
import threading

from tqdm import tqdm
from loguru import logger

from app.settings.configs import PORT, UTF_8, PASSCODE_MESSAGE

"""
=======================================================================

                host server

=======================================================================
"""
class ConnectionGame(object):
    def __init__(self, **kwargs):
        self.SERVER_SOCKET = {}
        self.CONNECTION = {}
        self.loginthread = {}
        self.names = {}
        self.DISCONNECTED_PLAYERS = []
        self.screen = kwargs.get("screen", {})
        self.__ip_public_input = kwargs.get("ip_public", None)
        self.port_input = kwargs.get("port", None)
        self.port_server = int(PORT)
        self.utf_8 = UTF_8
        self.pass_code_message = PASSCODE_MESSAGE
        self.passcode_host_server = None

        self._local_ip, self._public_ip = self.get_host_server()
        
        #fixed reconnect
        self.current_team = []

        if self._public_ip is None:
            raise Exception("Can't get Public IP address, Plase check your internet connection | Please check log file ../app/log")
        
    def random_passcode_host_server(self):
        # random number 6 digits
        return "".join([str(random.randint(0, 9)) for _ in range(6)])

    def get_host_server(self):
        local_ip = None
        public_ip = None
        
        with tqdm(total=3, desc="Getting host server", unit="step") as pbar:
            try:
                pbar.set_description("Getting local IP")
                local_ip = socket.gethostbyname(socket.gethostname())
                pbar.update(1)
            except Exception as e:
                logger.error(e)

            try:
                pbar.set_description("Getting public IP")
                response = requests.get('https://ifconfig.me/ip')
                public_ip = response.text.strip()
                pbar.update(1)
            except Exception as e:
                logger.error(e)

            pbar.set_description("\nLogging IP addresses")
            pbar.update(1)

        logger.debug(f"local_ip: {local_ip} | public_ip: {public_ip}")
        return local_ip, public_ip

    def init_host_server(self):
        exception_ = None
        try:
            # Create a socket object
            server_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)

            # Bind the socket to the host and port
            server_socket.bind((self._local_ip, self.port_server))

            # Listen for incoming connections
            server_socket.listen(1)
            logger.debug(f"Server is listening on {self._local_ip}:{self.port_server}")

            self.SERVER_SOCKET = server_socket
        except Exception as e:
            logger.error(f"init_host_server | public_ip: {self._local_ip} | port: {self.port_server} | exception: {e}")
            exception_ = e
        finally:
            return exception_
    
    def client_connect(self):
        
        client_socket, client_id, __exception__ = None, None, None
        try:
            # Create a socket object
            client_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)

            # Connect to the server
            ip_connect = self.__ip_public_input if self.__ip_public_input else self._local_ip
            port_connect = self.port_input

            client_socket.connect((ip_connect, port_connect))
            logger.debug("Connected to server")

            # Generate a unique identifier
            client_id = str(uuid.uuid4())

            # Send data to the server
            message = f"Hello, server! Client ID:{client_id}"
            client_socket.sendall(message.encode())
        except Exception as e:
            __exception__ = f"{ip_connect}:{port_connect} | {e}"
            logger.error(__exception__)
        finally:
 
            logger.debug(f"---------------{client_socket}, {client_id}, {__exception__}-----------------")
            return client_socket, client_id, __exception__

    def get_name(self, client_id):
        logger.debug(f"self.CONNECTION : {self.CONNECTION}")
        
        CONNECTION_player = self.CONNECTION[client_id]["client_socket"]
        logger.debug(f"waiting_recv_name | {CONNECTION_player}")
        self.names[client_id] = self.CONNECTION[client_id]["client_socket"].recv(16).decode(self.utf_8)
        name = self.names[client_id]

        logger.debug(f"recv_name | {name}")
        logger.debug(f"{self.names[client_id]} Log in")
        return self.names[client_id]

    def get_passcode(self, client_id):
        logger.debug(f"self.CONNECTION : {self.CONNECTION[client_id]}")
        client_passcode = None
        
        while not client_passcode:
            client_passcode = self.CONNECTION[client_id]["client_socket"].recv(16).decode(self.utf_8)
            logger.debug(f"recv_passcode | {client_passcode}")

            if client_passcode != self.passcode_host_server:
                self.CONNECTION[client_id]["client_socket"].send(self.pass_code_message.encode(self.utf_8))
                logger.debug(f"send_passcode_message | {self.pass_code_message}")
                raise Exception(self.pass_code_message)
            
            time.sleep(2)
            self.pass_code_message = "Passcode is correct"
            self.CONNECTION[client_id]["client_socket"].send(self.pass_code_message.encode(self.utf_8))
            logger.debug(f"send_passcode_message | {self.pass_code_message}")

        logger.debug(f"client_passcode | {client_passcode}")
        return client_passcode

    def server_wating_for_connection(self):
        logger.debug(f"server_wating_for_connection | Wating for connection")

        # Accept a client connection
        client_socket, client_address = self.SERVER_SOCKET.accept()
        logger.debug('server_wating_for_connection | Client connected IP = {}:{}'.format(client_address[0], client_address[1]))

        # Receive data from the client
        data = client_socket.recv(1024).decode('utf-8')
        client_id = data.split(":")[1]
        logger.debug('server_wating_for_connection | Received data from client: {}'.format(data))
        logger.debug('server_wating_for_connection | Client ID: {}'.format(client_id))
        
        self.CONNECTION[client_id] = {}
        self.CONNECTION[client_id]["client_socket"] = client_socket
        if "A" not in self.current_team:
            name = "A"
            self.names[client_id] = name
            self.CONNECTION[client_id]["name"] = name
            self.current_team.append(name)
        elif "A" in self.current_team and "B" not in self.current_team:
            name = "B"
            self.names[client_id] = name
            self.CONNECTION[client_id]["name"] = name
            self.current_team.append(name)
        logger.debug(f"server_wating_for_connection | CONNECTION PLAYERS: {self.CONNECTION[client_id]} | total_connection: {len(self.CONNECTION)}")
        if len(self.CONNECTION) == 2:
            return True

    def handle_player(self, client_id):
        response_access = self.get_passcode(client_id)
        if isinstance(response_access, Exception):
            raise Exception(response_access)
        
        name_player = self.get_name(client_id)
        logger.debug(f"handle_player started | name_player : {name_player} | response_access : {response_access}")
        return name_player

    def get_name_and_passcode(self):
        self.passcode_host_server = self.random_passcode_host_server()
        logger.debug(f"ConnectionGame | passcode_host_server: {self.passcode_host_server}")
        try:
            logger.debug(f"get_name_and_passcode | start")
            while len(self.CONNECTION) < 2:
                status_connected = self.server_wating_for_connection()
                logger.debug(f"get_name_and_passcode | server_wating_for_connection | status_connected : {status_connected}")

            logger.debug(f"get_name_and_passcode | all players connected | self.CONNECTION : {self.CONNECTION}")
            for client_id in self.CONNECTION:
                if client_id not in self.loginthread:
                    self.loginthread[client_id] = threading.Thread(
                        target=self.handle_player, 
                        args=(client_id,)
                    )

            [self.loginthread[client_id].start() for client_id in self.loginthread]
            [self.loginthread[client_id].join() for client_id in self.loginthread]
            logger.debug(f"loginthread started | all players connected | self.loginthread : {self.loginthread}")

            [self.CONNECTION[client_id]["client_socket"].send(self.CONNECTION[client_id]["name"].encode(self.utf_8)) for client_id in self.CONNECTION]
            logger.debug("send_player_A")
            logger.debug("send_player_B")

            [self.screen.server_check_player_join(self.names[client_id]) for client_id in self.names]
            logger.debug(f"get_name_and_passcode | end")
            return True
        except Exception as e:
            logger.error(f"get_name_and_passcode | Exception : {e}")
            return e

    def waiting_reconnect(self, delete_client_id,player_name):
        if player_name == "A":
            self.current_team = ["B"]
        else:
            self.current_team = ["A"]
        logger.debug(f"waiting_reconnect | delete_client_id : {delete_client_id}")
        logger.debug(f"waiting_reconnect | self.DISCONNECTED_PLAYERS {self.DISCONNECTED_PLAYERS}")
        logger.debug(f"waiting_reconnect | len(self.CONNECTION) : {len(self.CONNECTION)}")
        logger.debug(f"waiting_reconnect | len(self.loginthread) : {len(self.loginthread)}")
        logger.debug(f"waiting_reconnect | len(self.DISCONNECTED_PLAYERS) {len(self.DISCONNECTED_PLAYERS)}")
        try:
            if len(self.DISCONNECTED_PLAYERS) > 0:
                self.screen.waitingscreen()
                self.screen.update()

                message = f"Waiting for players to connect..."
                self.screen.widgets["waiting"].config(text=message)
                self.screen.update()
                logger.debug(f"waiting_reconnect | {message}")

                while len(self.CONNECTION) < 2:
                    status_connected = self.server_wating_for_connection()
                    time.sleep(0.5)

                logger.debug(f"waiting_reconnect | all players connected | self.CONNECTION : {self.CONNECTION}")
                name_player = None
                for client_id in self.CONNECTION:
                    name = self.CONNECTION[client_id]["name"]
                    if client_id not in self.loginthread:
                        logger.debug(f"waiting_reconnect | connecting.... name : {name}")
                        name_player = self.handle_player(client_id)
                        if isinstance(name_player, Exception):
                            raise Exception(name_player)

                        self.loginthread[client_id] = name_player
                        self.CONNECTION[client_id]["client_socket"].send(self.CONNECTION[client_id]["name"].encode(self.utf_8))
                        time.sleep(0.5)
                        self.CONNECTION[client_id]["client_socket"].send(str(self.screen.policy).encode(self.utf_8))
                        self.screen.server_check_player_join(self.names[client_id])
                        logger.debug(f"waiting_reconnect | connected name_player : {name_player}")
                        break

                if name_player:
                    logger.debug(f"waiting_reconnect | self.DISCONNECTED_PLAYERS : {self.DISCONNECTED_PLAYERS} | delete_client_id : {delete_client_id}")
                    self.DISCONNECTED_PLAYERS.remove(delete_client_id)
                    logger.debug(f"waiting_reconnect | DISCONNECTED_PLAYERS : {self.DISCONNECTED_PLAYERS}")
                return True
        except Exception as e:
            logger.error(f"waiting_reconnect | Exception : {e}")
            return e

def input_public_ip_port():

    ip_public, port, _exception = None, None, None
    try:
        while not ip_public:
            ip_public = input("Enter public IP address: ")
            if not validate_ip_address(ip_public):
                raise Exception("Invalid IP address")

        while not port:
            port = input("Enter port: ")
            if not validate_port(port):
                raise Exception("Invalid port number")

    except Exception as _exception:
        logger.error(_exception)

    finally:
        if not ip_public:
            raise Exception("ip_public is None")
        if not port:
            raise Exception("port is None")

        return {"ip_public": str(ip_public), "port": int(port), "exception": _exception}

def validate_ip_address(ip_address):
    # Regular expression pattern to match IPv4 addresses
    pattern = r"^(?:[0-9]{1,3}\.){3}[0-9]{1,3}$"
    return re.match(pattern, ip_address) is not None

def validate_port(port):
    # Regular expression pattern to match port numbers (1-65535)
    pattern = r"^(?:[1-9]|[1-9][0-9]{1,3}|[1-5][0-9]{4}|6[0-4][0-9]{3}|65[0-4][0-9]{2}|655[0-2][0-9]|6553[0-5])$"
    return re.match(pattern, port) is not None
