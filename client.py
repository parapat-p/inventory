from loguru import logger

import app.libs.interface as gui
from app.utilities.connection import ConnectionGame, input_public_ip_port
from app.utilities.action_game_client import ActionGameClients
from app.utilities.logger_util import LoggerUtil

try:
    # TODO : COMMENT THIS LINE | FOR TEST | ip_public="192.168.1.38" , port="50240"
    # dict_input = {"ip_public": "192.168.1.38",
    #                 "port": "50240"}
    
    # TODO : UNCOMMENT THIS LINE | FOR PRODUCTION
    dict_input = input_public_ip_port()
    if dict_input["exception"]:
        raise Exception(dict_input["exception"])
    
    public_ip, port = dict_input["ip_public"], dict_input["port"]

    LoggerUtil()
    connection_game = ConnectionGame(public_ip=public_ip, port=port)
    client_socket, client_id, __exception__ = connection_game.client_connect()
    if isinstance(client_socket, Exception):
        raise Exception(client_socket)
    
    logger.debug(f"client_connect started : {client_socket}")
    screen = gui.User_GUI()
    action_game = ActionGameClients(screen=screen, client_socket=client_socket, client_id=client_id)
    screen.widgets["loginButton"].config(command=action_game.client_login)
    screen.widgets["confirmButton"].config(command=action_game.client_confirm_order)
    screen.widgets["noButton"].config(command=action_game.client_make_no_order)
    screen.set()
    screen.mainloop()
    client_socket.close() if client_socket else None

except KeyboardInterrupt:
    if client_socket:
        client_socket.close()
    # Perform any other necessary cleanup tasks
    # ...
