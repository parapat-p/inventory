import time
import threading
import tkinter as tk

from tqdm import tqdm
from loguru import logger

from app.settings.configs import UTF_8, PASSCODE_MESSAGE

class ActionGameClients(object):
    def __init__(self, **kwargs):
        self.screen = kwargs.get("screen", {})
        self.client_socket = kwargs.get("client_socket", {})
        self.client_id = kwargs.get("client_id", "")
        self.utf_8 = UTF_8
        self.pass_code_message = PASSCODE_MESSAGE
        self.make_order = 0
        self.starting = True

        self.execute = {
            "":self.client_handler,
            "next":self.client_next_turn,
            "get_EOQ":self.client_get_EOQ,
            "close":self.client_closing,
            "restart":self.client_restart,
            "closed":self.client_recv_closed,
            "skip":self.client_skip_turn
        }

    def client_execute_command(self, command):
        if command in self.execute:
            logger.debug(f"executing {command}")
            self.execute[command]()
        else:
            logger.debug(f"command '{command}' don't exists.")

    def client_recv_command(self):
    	while True:
            logger.debug("waiting_client_recv_command")
            command = self.client_socket.recv(16).decode(self.utf_8)
            logger.debug(f"client_recv_command_{command}")
            self.client_execute_command(command)

    def client_login(self):
        try:
            self.screen.waitingscreen()
            self.screen.update()
            self.client_socket.send(self.screen.passcode.encode(self.utf_8) if self.screen.passcode else "-".encode(self.utf_8))
            logger.debug(f"client_login | self.screen.passcode : {self.screen.passcode}")
            server_access = str(self.client_socket.recv(512).decode(self.utf_8))
            logger.debug(f"client_login | recv_server_access : {server_access}")
            time.sleep(0.5)
    
            if server_access == self.pass_code_message:
                message = f"Error Server access denied : {server_access}"
                self.screen.widgets["waiting"].config(text=message)
                self.screen.update()
                self.client_socket.close()
                raise ConnectionError(f"ConnectionError: {message}")

            start_time = time.time()
            timeout = 120  # 2 minutes
            with tqdm(total=4, desc="Progress login", unit="sec") as progress_bar_login:
                # function : get_name of server (...\KU-Inventory-Lab\app\utilities\connection.py)
                self.client_socket.send(self.screen.name.encode(self.utf_8) if self.screen.name else "-".encode(self.utf_8))
                logger.debug(f"client_login | send self.screen.name : {self.screen.name}")
                progress_bar_login.update(1)  # progress_bar_login bar with the elapsed time
                
                if time.time() - start_time > timeout:
                    raise TimeoutError("Timeout: Condition not met within 2 minutes")
                
                # function : server_connection_with_player of server (...\KU-Inventory-Lab\app\utilities\connection.py | line 203)
                name_from_server = self.screen.policy = self.client_socket.recv(16).decode(self.utf_8)
                logger.debug(f"client_login | recv name_from_server : {name_from_server}")
                progress_bar_login.update(1)  # progress_bar_login bar with the elapsed time

                message = f"Waiting server select game mode"
                self.screen.widgets["waiting"].config(text=message)
                self.screen.update()
                progress_bar_login.update(1)  # progress_bar_login bar with the elapsed time

                # function : server_set_game of action_game_server (...\KU-Inventory-Lab\app\utilities\action_game_server.py | line 371)
                logger.debug("client_login | waiting_recv_policy")
                self.screen.policy = int(self.client_socket.recv(16).decode(self.utf_8))
                progress_bar_login.update(1)  # progress_bar_login bar with the elapsed time

            self.screen.mainscreen()
            
            threading.Thread(target=self.client_recv_command, daemon=True).start()
        except KeyboardInterrupt:
            # Handle any cleanup tasks specific to the client_login method
            raise  # Re-raise the KeyboardInterrupt exception to stop the execution

    def client_confirm_order(self):
        self.screen.confirm_order()
        self.make_order = 1
        self.client_socket.send("ordered".encode(self.utf_8))
        logger.debug("send_ordered")

    def client_make_no_order(self):
        self.screen.make_no_order()
        self.make_order = 1
        self.client_socket.send("ordered".encode(self.utf_8))
        logger.debug("send_ordered")

    def client_handler(self):
        pass

    def client_recv_closed(self):
        pass

    def client_closing(self):
        self.client_socket.close()
        self.screen.destroy()

    def client_next_turn(self, skip=0):
        
        self.screen.widgets["confirmButton"].config(state=tk.DISABLED)
        self.screen.widgets["cancelButton"].config(state=tk.DISABLED)
        self.screen.widgets["yesButton"].config(state=tk.DISABLED)
        self.screen.widgets["noButton"].config(state=tk.DISABLED)
        
        if self.screen.policy:
            if (not self.make_order)*self.starting:
                self.client_socket.send("not ordered".encode(self.utf_8))
                logger.debug("send_not_ordered")
                logger.debug("waiting_recv_closed")
                closed = self.client_socket.recv(16).decode(self.utf_8)
                logger.debug("recv_closed")
            self.client_socket.send("ready".encode(self.utf_8))
            logger.debug("send_ready")
            logger.debug("waiting_recv_skip")
            skip = int(self.client_socket.recv(16).decode(self.utf_8))
            logger.debug("recv_skip")
            
            self.starting = False
        else:
            if not self.make_order:
                self.client_socket.send("not ordered".encode(self.utf_8))
                logger.debug("send_not_ordered")
                logger.debug("waiting_recv_closed")
                closed = self.client_socket.recv(16).decode(self.utf_8)
                logger.debug("recv_closed")
            self.client_socket.send(str(self.screen.order if self.screen.order else 0).encode(self.utf_8))
            logger.debug("send_order")
        self.make_order =0
        logger.debug("waiting_recv_eval")
        output = eval(self.client_socket.recv(1024).decode(self.utf_8))
        logger.debug("recv_eval")
        self.client_socket.send("received".encode(self.utf_8))
        logger.debug("send_received")
        self.screen.next_turn(output, skip)
        
        self.screen.widgets["confirmButton"].config(state=tk.NORMAL)
        self.screen.widgets["cancelButton"].config(state=tk.NORMAL)
        self.screen.widgets["yesButton"].config(state=tk.DISABLED if self.screen.onorder else tk.NORMAL)
        self.screen.widgets["noButton"].config(state=tk.DISABLED if self.screen.onorder else tk.NORMAL)

    def client_get_EOQ(self):
        self.client_socket.send(f"{{'EOQ':{self.screen.EOQ}, 'ROP':{self.screen.ROP}}}".encode(self.utf_8))
        logger.debug("send_EOQ")

    def client_restart(self):
        
        if (not self.screen.policy)+(not self.make_order)*self.starting:
            self.client_socket.send("not ordered".encode(self.utf_8))
            logger.debug("send_not_ordered")
            logger.debug("waiting_recv_closed")
            closed = self.client_socket.recv(16).decode(self.utf_8)
            logger.debug("recv_closed | closed : "+str(closed))

        self.client_socket.send("ready".encode(self.utf_8))
        logger.debug("send_ready")
        self.screen.reset()
        self.screen.waitingscreen()
        logger.debug("waiting_recv_policy")
        self.screen.policy = int(self.client_socket.recv(16).decode(self.utf_8))
        logger.debug("recv_policy | policy : "+str(self.screen.policy))
        self.screen.mainscreen()
 
    def client_skip_turn(self):
        
        if self.screen.policy:
            if (not self.make_order)*self.starting:
                self.client_socket.send("not ordered".encode(self.utf_8))
                logger.debug("send_not_ordered")
                logger.debug("waiting_recv_closed")
                closed = self.client_socket.recv(16).decode(self.utf_8)
                logger.debug("recv_closed")
            self.client_socket.send("ready".encode(self.utf_8))
            logger.debug("send_ready")
            logger.debug("waiting_recv_skip")
            skip = int(self.client_socket.recv(16).decode(self.utf_8))
            logger.debug("recv_skip")
            
            self.starting = False
        else:
            if not self.make_order:
                self.client_socket.send("not ordered".encode(self.utf_8))
                logger.debug("send_not_ordered")
                logger.debug("waiting_recv_closed")
                closed = self.client_socket.recv(16).decode(self.utf_8)
                logger.debug("recv_closed")
            self.client_socket.send(str(self.screen.order if self.screen.order else 0).encode(self.utf_8))
            logger.debug("send_order")
        self.make_order =0
        logger.debug("waiting_recv_eval_list")
        output = eval(self.client_socket.recv(1048576).decode(self.utf_8))
        logger.debug("recv_eval_list")
        self.client_socket.send("received".encode(self.utf_8))
        logger.debug("send_received")
        [
            (
                self.screen.next_turn(i, skip=1),
                time.sleep(.6)
            )
            for i in output
        ]