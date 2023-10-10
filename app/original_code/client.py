import sys
import socket
import time
import threading
import tkinter as tk
from tkinter import ttk

# import utils
import libs.interface as gui

"""
=======================================================================

				connect server

=======================================================================
"""

HOST = str(sys.argv[1]) #IP Address
PORT = 50240

SERVER = socket.socket()
SERVER.connect((HOST, PORT))
print(f"IP: {HOST}\nPort: {PORT}")

"""
=======================================================================
=======================================================================

				MAIN PROGRAM

=======================================================================
=======================================================================
"""
make_order = 0
starting = True

def login():
	screen.waitingscreen()
	screen.update()
	SERVER.send(screen.name.encode("UTF-8") if screen.name else "-".encode("UTF-8"))
	print("send_name")
	start = ""
	
	while not start in ["A", "B"]:
		print("waiting_recv_player")
		start = SERVER.recv(16).decode("UTF-8")
		print("recv_player")

		print (f"start as player {start}")
	
	screen.widgets["waiting"].config(text="starting...")
	screen.update()
	
	print("waiting_recv_policy")
	screen.policy = int(SERVER.recv(16).decode("UTF-8"))
	print("recv_policy")
	
	screen.mainscreen()
	threading.Thread(target=recv_command, daemon=True).start()

def confirm_order():
	global make_order
	
	screen.confirm_order()
	make_order = 1
	SERVER.send("ordered".encode("UTF-8"))
	print("send_ordered")

def make_no_order():
	global make_order
	
	screen.make_no_order()
	make_order = 1
	SERVER.send("ordered".encode("UTF-8"))
	print("send_ordered")

screen = gui.User_GUI()
screen.widgets["loginButton"].config(command=login)
screen.widgets["confirmButton"].config(command=confirm_order)
screen.widgets["noButton"].config(command=make_no_order)
screen.set()

def handler():
	pass

def recv_closed():
	pass

def closing():
	SERVER.close()
	screen.destroy()

def next_turn(skip=0):
	global make_order
	global starting
	
	screen.widgets["confirmButton"].config(state=tk.DISABLED)
	screen.widgets["cancelButton"].config(state=tk.DISABLED)
	screen.widgets["yesButton"].config(state=tk.DISABLED)
	screen.widgets["noButton"].config(state=tk.DISABLED)
	
	if screen.policy:
		if (not make_order)*starting:
			SERVER.send("not ordered".encode("UTF-8"))
			print("send_not_ordered")
			print("waiting_recv_closed")
			closed = SERVER.recv(16).decode("UTF-8")
			print("recv_closed")
		SERVER.send("ready".encode("UTF-8"))
		print("send_ready")
		print("waiting_recv_skip")
		skip = int(SERVER.recv(16).decode("UTF-8"))
		print("recv_skip")
		
		starting = False
	else:
		if not make_order:
			SERVER.send("not ordered".encode("UTF-8"))
			print("send_not_ordered")
			print("waiting_recv_closed")
			closed = SERVER.recv(16).decode("UTF-8")
			print("recv_closed")
		SERVER.send(str(screen.order if screen.order else 0).encode("UTF-8"))
		print("send_order")
	make_order =0
	print("waiting_recv_eval")
	output = eval(SERVER.recv(1024).decode("UTF-8"))
	print("recv_eval")
	SERVER.send("received".encode("UTF-8"))
	print("send_received")
	screen.next_turn(output, skip)
	
	screen.widgets["confirmButton"].config(state=tk.NORMAL)
	screen.widgets["cancelButton"].config(state=tk.NORMAL)
	screen.widgets["yesButton"].config(state=tk.DISABLED if screen.onorder else tk.NORMAL)
	screen.widgets["noButton"].config(state=tk.DISABLED if screen.onorder else tk.NORMAL)

def get_EOQ():
	SERVER.send(f"{{'EOQ':{screen.EOQ}, 'ROP':{screen.ROP}}}".encode("UTF-8"))
	print("send_EOQ")

def restart():
	global starting
	
	if (not screen.policy)+(not make_order)*starting:
		SERVER.send("not ordered".encode("UTF-8"))
		print("send_not_ordered")
		print("waiting_recv_closed")
		closed = SERVER.recv(16).decode("UTF-8")
		print("recv_closed")
	SERVER.send("ready".encode("UTF-8"))
	print("send_ready")
	screen.reset()
	screen.waitingscreen()
	print("waiting_recv_policy")
	screen.policy = int(SERVER.recv(16).decode("UTF-8"))
	print("recv_policy")
	screen.mainscreen()

def skip_turn():
	global make_order
	global starting
	
	if screen.policy:
		if (not make_order)*starting:
			SERVER.send("not ordered".encode("UTF-8"))
			print("send_not_ordered")
			print("waiting_recv_closed")
			closed = SERVER.recv(16).decode("UTF-8")
			print("recv_closed")
		SERVER.send("ready".encode("UTF-8"))
		print("send_ready")
		print("waiting_recv_skip")
		skip = int(SERVER.recv(16).decode("UTF-8"))
		print("recv_skip")
		
		starting = False
	else:
		if not make_order:
			SERVER.send("not ordered".encode("UTF-8"))
			print("send_not_ordered")
			print("waiting_recv_closed")
			closed = SERVER.recv(16).decode("UTF-8")
			print("recv_closed")
		SERVER.send(str(screen.order if screen.order else 0).encode("UTF-8"))
		print("send_order")
	make_order =0
	print("waiting_recv_eval_list")
	output = eval(SERVER.recv(1048576).decode("UTF-8"))
	print("recv_eval_list")
	SERVER.send("received".encode("UTF-8"))
	print("send_received")
	[
		(
			screen.next_turn(i, skip=1),
			time.sleep(.6)
		)
		for i in output
	]

execute = {
	"":handler,
	"next":next_turn,
	"get_EOQ":get_EOQ,
	"close":closing,
	"restart":restart,
	"closed":recv_closed,
	"skip":skip_turn
}

def execute_command(command):
	if command in execute:
		print(f"executing {command}")
		execute[command]()
	else:
		print(f"command '{command}' don't exists.")

def recv_command():
	while True:
		print("waiting_recv_command")
		command = SERVER.recv(16).decode("UTF-8")
		print(f"recv_command_{command}")
		execute_command(command)

screen.mainloop()

SERVER.close() if SERVER else None
