from loguru import logger

import app.libs.interface as gui
from app.utilities.connection import ConnectionGame
from app.utilities.action_game_server import ActionGameServers
from app.utilities.logger_util import LoggerUtil

try:
    connection_game = None
    LoggerUtil()

    screen = gui.Front_screen()
    screen.set()
    connection_game = ConnectionGame(screen=screen)
    exception_ = connection_game.init_host_server()
    if isinstance(exception_, Exception):
        raise Exception(exception_)
    logger.debug(f"init_host_server started")
    
    response_connection = connection_game.get_name_and_passcode()
    if isinstance(response_connection, Exception):
        raise Exception(response_connection)
    
    action_game = ActionGameServers(screen=screen, 
                                    connection_game=connection_game, 
                                    CONNECTION=connection_game.CONNECTION, 
                                    DISCONNECTED_PLAYERS=connection_game.DISCONNECTED_PLAYERS,
                                    loginthread=connection_game.loginthread)
    logger.debug(f"ActionGameServers started: {action_game}")

    screen.widgets["saveButton"].config(command=action_game.server_savefile)
    screen.widgets["mode1Button"].config(command=lambda: action_game.server_set_game(0))
    screen.widgets["mode2Button"].config(command=lambda: action_game.server_set_game(1))
    screen.widgets["restartButton"].config(command=action_game.server_restart)

    screen.starting()
    screen.mainloop()

    message = "close"
    [connection_game.CONNECTION[player].send(message.encode(connection_game.utf_8)) for player in connection_game.CONNECTION]
    logger.debug("send_command_close_A")

    connection_game.SERVER_SOCKET.close()

except Exception as e:
    logger.error(e)
    
    if connection_game:
        connection_game.SERVER_SOCKET.close()

    if screen:
        screen.destroy()

    # Perform any other necessary cleanup tasks
    # ...