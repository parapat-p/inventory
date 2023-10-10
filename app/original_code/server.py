import os
import csv
import socket
import time
import threading
import tkinter as tk
from tkinter import ttk
import xlwings as xw
from bokeh.io import output_file, show
from bokeh.layouts import column, layout, row
from bokeh.plotting import figure
from bokeh.models import CheckboxGroup, ColumnDataSource, CustomJS, Label

# import utils
import libs.interface as gui

"""
=======================================================================

				host server

=======================================================================
"""
try:
	HOST = [
		(s.connect(("1.1.1.1", 80)), s.getsockname(), s.close)
		for s in [socket.socket()]
	][0][1][0] #IP Address
except:
	HOST = socket.gethostbyname(socket.gethostname())

PORT = 50240

STREAMING = True
ROOM = ("A", "B")
CONNECTION = {}

loginthread = {}
receivethread = {}
xlthread = {}
outputthread = {}

names = {}
order = {}
EOQ = {}

SERVER = socket.socket()

instance = None
tnow = None
path_save = os.path.abspath("./save")

SERVER.bind((HOST, PORT))
SERVER.listen()
print(f"IP: {HOST}\nPort: {PORT}")

"""
=======================================================================

				excel book

=======================================================================
"""

# if not xw.apps:
# 	xw.App()
# app = xw.apps[xw.apps.keys()[0]]

# if not "Inventory_Lab.xlsx" in [wb.name for wb in app.books]:
# 	app.books.open("Inventory_Lab.xlsx")
# Inv = {sheet.name:sheet for sheet in xw.books["Inventory_Lab.xlsx"].sheets}

Inv = xw.Book("Inventory_Lab.xlsx").sheets

"""
=======================================================================
=======================================================================

				MAIN PROGRAM

=======================================================================
=======================================================================
"""

duration = int(Inv["CONFIG"]["F14"].value)
init_position = 0 # int(Inv["CONFIG"]["F15"].value if Inv["CONFIG"]["F15"].value else 0)
position = init_position
policy = 0
Cost = []

def connect(player):
	if not player in CONNECTION:
		CONNECTION[player] = SERVER.accept()
		print(CONNECTION[player][1])

def get_name(player):
	# names[player] = None
	# while not eval(names[player]):
	names[player] = ""
	while not names[player]:
		print(f"waiting_recv_name_{player}")
		names[player] = CONNECTION[player][0].recv(16).decode("UTF-8")
		print(f"recv_name_{player}")
	print(f"{names[player]} Log in")

def receive_order(player):
	print(f"waiting_recv_ordering_{player}")
	receive = CONNECTION[player][0].recv(16).decode("UTF-8")
	print(f"recv_ordering_{player}")
	if receive == "ordered":
		screen.receive_order(player)
		CONNECTION[player][0].send("closed".encode("UTF-8"))
		print(f"send_command_closed_{player}")
	elif receive == "not ordered":
		CONNECTION[player][0].send("closed".encode("UTF-8"))
		print(f"send_command_closed_{player}")
	print("thread closed")

[connect(player) for player in ROOM]

screen = gui.Front_screen()
screen.set()

for player in CONNECTION:
	loginthread[player] = threading.Thread(
		target = get_name,
		args = (player,),
	)

[loginthread[player].start() for player in loginthread]
[loginthread[player].join() for player in loginthread]

# time.sleep(2)
print("starting")

[CONNECTION[player][0].send(player.encode("UTF-8")) for player in CONNECTION]
print("send_player_A")
print("send_player_B")

[screen.connecting(names[player]) for player in names]

def wait_order():
	for player in CONNECTION:
		receivethread[player] = threading.Thread(
			target = receive_order,
			args = (player,),
		)
	
	[receivethread[player].start() for player in receivethread]

def next_turn(skip=0):
    global position
	global duration
	global policy
	
	screen.widgets["nextButton"].config(state=tk.DISABLED)
	screen.widgets["skipButton"].config(state=tk.DISABLED)
	screen.clear_order()
	
	for player in CONNECTION:
		CONNECTION[player][0].send("next".encode("UTF-8"))
		print(f"send_command_next_{player}")

		receivethread[player].join()
		if policy:
			print(f"waiting_recv_ready_{player}")
			ready = CONNECTION[player][0].recv(16).decode("UTF-8")
			print(f"recv_ready_{player}")
			CONNECTION[player][0].send(str(skip).encode("UTF-8"))
			print(f"send_skip_{player}")
			Inv[player][(2+position, 11)].value = Inv[player][(2+position, 12)].value
		else:
			print(f"waiting_recv_order_{player}")
			order[player] = CONNECTION[player][0].recv(16).decode("UTF-8")
			print(f"recv_order_{player}")
			Inv[player][(2+position, 11)].value = order[player]
	screen.edit_score(
		position,
		"Ordering",
		A=[int(Inv["A"][(2+position, 16)].value)],
		B=[int(Inv["B"][(2+position, 16)].value)],
	) if position - init_position else None
	
	screen.set_total(
		profit=[int(Inv[team]["X16"].value) for team in CONNECTION],
		# fix=[-int(Inv[team]["X12"].value) for team in CONNECTION],
		var=[-int(Inv[team]["X17"].value) for team in CONNECTION],
	)
	
	position = position + 1
	# Inv["CONFIG"]["F15"].value = position
	screen.add_score(
		position,
		skip = skip,
		A = [
			int(i) if i else 0
			for col in [(2, 3), (7, 7), (10, 10), (4, 4), (9, 9), (15, 19)]
			for i in Inv["A"].range(
				(3+position, col[0]),
				(3+position, col[1]),
			).options(ndim=1).value
		],
		Main = [int(i) for i in Inv["CONFIG"].range(
			(3+position, 2),
			(3+position, 3),
		).value],
		B = [
			int(i) if i else 0
			for col in [(2, 3), (7, 7), (10, 10), (4, 4), (9, 9), (15, 19)]
			for i in Inv["B"].range(
				(3+position, col[0]),
				(3+position, col[1]),
			).options(ndim=1).value
		],
	)
	# (
	# 	screen.set_leftover(*[int(Inv[team]["X16"].value) for team in CONNECTION], *[int(Inv[team][(2+position, 9)].value) for team in CONNECTION])
	# 	if position >= duration else screen.set_total(*[int(Inv[team]["X16"].value) for team in CONNECTION])
	# )
	screen.update()
	
	for player in CONNECTION:
		CONNECTION[player][0].send(
			f"""{{
				'period':{position},
				'demand':{Inv[player][(2+position, 2)].value},
				'onhand':{Inv[player][(2+position, 9)].value},
				'onorder':{Inv[player][(2+position, 3)].value},
				'arrive':{Inv[player][(2+position, 4)].value},
				'receive':{Inv[player][(2+position, 5)].value},
				'sold':{Inv[player][(2+position, 7)].value},
				'Shortage':{Inv[player][(2+position, 8)].value},
				'profits':{Inv[player]['X16'].value},
				'varcost':{-Inv[player]['X17'].value},
			}}""".encode('UTF-8')
		)
		print(f"send_eval_{player}")
	
	for player in CONNECTION:
		print(f"waiting_recv_received_{player}")
		received = CONNECTION[player][0].recv(16).decode("UTF-8")
		print(f"recv_received_{player}")
	
	if not skip:
		time.sleep(2)
		screen.widgets["Title"]["day"]["text"] = f"END OF DAY"
		screen.widgets["Title"]["demand"]["text"] = position
	
	if position < duration:
		screen.widgets["nextButton"].config(state=tk.NORMAL)
		screen.widgets["skipButton"].config(state=tk.NORMAL)
		wait_order() if not policy else None
	else:
		screen.game_over(
			A_game_var=-int(Inv["A"]["X17"].value),
			A_game_cycle=round(Inv["A"]["AB13"].value, 4),
			A_true_var=-int(Inv["RESULT"]["C15"].value),
			A_true_cycle=round(Inv["RESULT"]["C19"].value, 4),
			B_game_var=-int(Inv["B"]["X17"].value),
			B_game_cycle=round(Inv["B"]["AB13"].value, 4),
			B_true_var=-int(Inv["RESULT"]["D15"].value),
			B_true_cycle=round(Inv["RESULT"]["D19"].value, 4),
		) if policy else None
	print(position)
	
def split_send():
	pass

def xl(duration, position, player):
	step = 15
	print(position)
	for i in range((duration-position)//step):
		Inv[player][f"L{3+position+step*i}:L{3+position+step*(i+1)-1}"].formula2 = f"=M{3+position+step*i}"
		print(f"L{3+position+step*i}:L{3+position+step*(i+1)-1}")
		# Inv[player][f"L{3+position+step*i}:L{3+position+step*(i+1)-1}"].value = Inv[player][f"L{3+position+step*i}:L{3+position+step*(i+1)-1}"].value
	print((duration-position)%step)
	if (duration-position)%step:
		Inv[player][f"L{3+duration-(duration-position)%step}:L{3+duration-1}"].formula2 = f"=M{3+duration-(duration-position)%step}"
		print(f"L{3+duration-(duration-position)%step}:L{3+duration-1}")
		# Inv[player][f"L{3+duration+(duration-position)%step}:L{3+duration-1}"].value = Inv[player][f"L{3+duration+(duration-position)%step}:L{3+duration}"].value

def skip_turn(skip=0):
	global position
	global duration
	global policy
	
	screen.widgets["nextButton"].config(state=tk.DISABLED)
	screen.widgets["skipButton"].config(state=tk.DISABLED)
	screen.clear_order()
	
	for player in CONNECTION:
		CONNECTION[player][0].send("skip".encode("UTF-8"))
		print(f"send_command_skip_turn_{player}")
		
		receivethread[player].join()
		print(f"waiting_recv_ready_{player}")
		ready = CONNECTION[player][0].recv(16).decode("UTF-8")
		print(f"recv_ready_{player}")
		CONNECTION[player][0].send(str(skip).encode("UTF-8"))
		print(f"send_skip_{player}")
	
	for player in CONNECTION:
		xlthread[player] = threading.Thread(
			target = xl,
			args = (duration, position, player),
		)
	
	[xlthread[player].start() for player in xlthread]
		# for i in range(duration-position):
		# 	Inv[player][(2+position+i, 11)].value = Inv[player][(2+position+i, 12)].value
	
	for player in CONNECTION:
		output_send = f"""{[{
			'period':position+i+1,
			'demand':Inv[player][(2+position+i+1, 2)].value,
			'onhand':Inv[player][(2+position+i+1, 9)].value,
			'onorder':Inv[player][(2+position+i+1, 3)].value,
			'arrive':Inv[player][(2+position+i+1, 4)].value,
			'receive':Inv[player][(2+position+i+1, 5)].value,
			'sold':Inv[player][(2+position+i+1, 7)].value,
			'Shortage':Inv[player][(2+position+i+1, 8)].value,
			'profits':Inv[player]['X16'].value,
			'varcost':-Inv[player]['X17'].value,
		} for i in range(duration-position)]}""".encode('UTF-8')
		outputthread[player] = threading.Thread(
			target = CONNECTION[player][0].send,
			args = (output_send,),
		)
	[outputthread[player].start() for player in outputthread]
	print(f"send_eval_list_{player}")
	
	for player in CONNECTION:
		print(f"waiting_recv_received_{player}")
		received = CONNECTION[player][0].recv(16).decode("UTF-8")
		print(f"recv_received_{player}")
	
	for i in range(duration-position):
		screen.edit_score(
			position+i,
			"Ordering",
			A=[int(Inv["A"][(2+position+i, 16)].value)],
			B=[int(Inv["B"][(2+position+i, 16)].value)],
		) if position+i - init_position+i else None
		
		screen.set_total(
			profit=[int(Inv[team]["X16"].value) for team in CONNECTION],
			# fix=[-int(Inv[team]["X12"].value) for team in CONNECTION],
			var=[-int(Inv[team]["X17"].value) for team in CONNECTION],
		)
		
		# Inv["CONFIG"]["F15"].value = position+i
		screen.add_score(
			position+i+1,
			skip = skip,
			A = [
				int(j) if j else 0
				for col in [(2, 3), (7, 7), (10, 10), (4, 4), (9, 9), (15, 19)]
				for j in Inv["A"].range(
					(3+position+i+1, col[0]),
					(3+position+i+1, col[1]),
				).options(ndim=1).value
			],
			Main = [int(j) for j in Inv["CONFIG"].range(
				(3+position+i+1, 2),
				(3+position+i+1, 3),
			).value],
			B = [
				int(j) if j else 0
				for col in [(2, 3), (7, 7), (10, 10), (4, 4), (9, 9), (15, 19)]
				for j in Inv["B"].range(
					(3+position+i+1, col[0]),
					(3+position+i+1, col[1]),
				).options(ndim=1).value
			],
		)
		screen.update()
		time.sleep(.2)
		
	# screen.set_leftover(*[int(Inv[team]["X16"].value) for team in CONNECTION], *[int(Inv[team][(2+duration, 9)].value) for team in CONNECTION])
	
	# time.sleep(2)
	# screen.widgets["Title"]["day"]["text"] = f"END OF DAY"
	# screen.widgets["Title"]["demand"]["text"] = duration
	
	position = duration
	
	screen.game_over(
		A_game_var=-int(Inv["A"]["X17"].value),
		A_game_cycle=round(Inv["A"]["AB13"].value, 4),
		A_true_var=-int(Inv["RESULT"]["C15"].value),
		A_true_cycle=round(Inv["RESULT"]["C19"].value, 4),
		B_game_var=-int(Inv["B"]["X17"].value),
		B_game_cycle=round(Inv["B"]["AB13"].value, 4),
		B_true_var=-int(Inv["RESULT"]["D15"].value),
		B_true_cycle=round(Inv["RESULT"]["D19"].value, 4),
	) if policy else None


def skip():
	for _ in range(duration-position):
		next_turn(skip=1)

def set_game(val):
	global duration
	global position
	global policy
	
	duration = int(Inv["CONFIG"]["F14"].value)
	position = init_position
	
	screen.policy = val
	param_val = [*[int(i) for i  in Inv["CONFIG"]["F2:F4"].value], int(Inv["CONFIG"]["F6"].value), int(Inv["CONFIG"]["F8"].value), tuple([int(i) for i in Inv["CONFIG"]["F11:F12"].value])]
	screen.set_parameters(
		**{
			param:param_val[i]
			for i, param in enumerate(screen.parameters)
		}
	)
	
	Inv["CONFIG"]["C:C"].clear_contents()
	Inv["CONFIG"]["C2"].value = "Demand"
	Inv["CONFIG"]["C4"].formula2 = f"={Inv['CONFIG']['F16'].value}"
	Inv["CONFIG"]["C4"].value =[[v] for v in Inv["CONFIG"]["C4#"].value]
	
	[CONNECTION[player][0].send(str(screen.policy).encode("UTF-8")) for player in CONNECTION]
	print("send_policy_A")
	print("send_policy_B")
	
	for player in CONNECTION:
		if screen.policy:
			Inv[player]["X8"].formula2 = "=TRUE"
		else:
			Inv[player]["X8"].formula2 = "=FALSE"
		Inv[player]["L3:L4"].value = 1
		Inv[player]["L:L"].clear_contents()
		Inv[player]["L2"].value = "Order"
	
	screen.widgets["nextButton"].config(text="Start" if screen.policy else "Next", command=get_EOQ if screen.policy else next_turn)
	screen.widgets["skipButton"].config(command=skip_turn)
	
	Cost = screen.cost
	policy = screen.policy
	
	screen.mainscreen()
	wait_order()

def get_EOQ():
	for player in CONNECTION:
		CONNECTION[player][0].send("get_EOQ".encode("UTF-8"))
		print(f"send_command_get_EOQ_{player}")
		print(f"waiting_recv_EOQ_{player}")
		EOQ[player] = eval(CONNECTION[player][0].recv(64).decode("UTF-8"))
		print(f"recv_EOQ_{player}")
		Inv[player]["X5"].value = int(EOQ[player]["EOQ"])
		Inv[player]["X6"].value = int(EOQ[player]["ROP"])
		
		screen.widgets["nextButton"].config(text="Next", command=next_turn)
		screen.widgets["skipButton"].config(command=skip_turn)

def restart():
	screen.widgets["nextButton"].config(state=tk.NORMAL)
	screen.widgets["skipButton"].config(state=tk.NORMAL)
	
	order = {}
	EOQ = {}
	
	for player in CONNECTION:
		CONNECTION[player][0].send("restart".encode("UTF-8"))
		print(f"send_command_restart_{player}")
		Inv[player]["L:L"].clear_contents()
		Inv[player]["L2"].value = "Order"
		receivethread[player].join()
		print(f"waiting_recv_ready_{player}")
		ready = CONNECTION[player][0].recv(16).decode("UTF-8")
		print(f"recv_ready_{player}")
		screen.reset()

def result(path):
	global duration
	global policy
	
	output_file(path)
	alpha = .25
	
	data = {
		team:{
			"Day":[
				Inv[team][f"B3:B{duration+3}"].options(empty=float(0)).value[i//2]
				for i in range(2*len(Inv[team][f"B3:B{duration+3}"].options(empty=float(0)).value))
				if not i%2 or Inv[team][f"F4:F{duration+4}"].options(empty=float(0)).value[i//2] or Inv[team][f"L2:L{duration+2}"].options(empty=float(0)).value[i//2]
			],
			"Onhand":[
				Inv[team][f"J3:J{duration+3}"].options(empty=float(0)).value[i//2]
				if not i%2 else Inv[team][f"G4:G{duration+4}"].options(empty=float(0)).value[i//2]
				for i in range(2*len(Inv[team][f"B3:B{duration+3}"].options(empty=float(0)).value))
				if not i%2 or Inv[team][f"F4:F{duration+4}"].options(empty=float(0)).value[i//2] or Inv[team][f"L2:L{duration+2}"].options(empty=float(0)).value[i//2]
			],
			"OnOrder":[
				Inv[team][f"D3:D{duration+3}"].options(empty=float(0)).value[i//2]
				if bool(i%2) == bool(Inv[team][f"L2:L{duration+2}"].options(empty=float(0)).value[i//2]) else 0
				for i in range(2*len(Inv[team][f"B3:B{duration+3}"].options(empty=float(0)).value))
				if not i%2 or Inv[team][f"F4:F{duration+4}"].options(empty=float(0)).value[i//2] or Inv[team][f"L2:L{duration+2}"].options(empty=float(0)).value[i//2]
			],
		} for team in CONNECTION
	}

	line_source = {team:ColumnDataSource(data=data[team]) for team in CONNECTION}
	Inv_graph = figure(title="Inventory", height=500, width=1200)
	
	graph_lines = {
		team:Inv_graph.vline_stack(
			["Onhand", "OnOrder"],
			x="Day",
			source = line_source[team],
			line_dash = ["solid", "dashed"],
			color = "Red" if team == "A" else "Blue"
		) for team in CONNECTION
	}
	for team in CONNECTION:
		graph_lines[team][1].visible = False
	
	graph_labels = {
		f"{team}":Label(
			x = data[team]["Day"][-1],
			y = data[team]["Onhand"][-1],
			text = f"{team}_Inv"
		)
		for team in CONNECTION
	}

	graph_rop = {
		**{f"{team}_line":Inv_graph.line(x=[data[team]["Day"][0], data[team]["Day"][-1]], y=[EOQ[team]["ROP"], EOQ[team]["ROP"]], line_dash="dotted", color="Red" if team == "A" else "Blue") for team in CONNECTION},
		**{f"{team}_label":Label(x=data[team]["Day"][-1], y=EOQ[team]["ROP"], text=f"{team}_Reorder_Point") for team in CONNECTION},
	} if policy else None
	
	[Inv_graph.add_layout(graph_labels[team]) for team in graph_labels]
	[Inv_graph.add_layout(graph_rop[key]) for key in graph_rop] if graph_rop else None

	checkbox_team = CheckboxGroup(labels=["Team_A", "Team_B"], active=[0, 1], width=100)
	checkbox_lines = CheckboxGroup(labels=["On Hand", "Stock Position", "ROP"], active=[0, 2], width=100)
	check = CustomJS(
		args=dict(
			lines=graph_lines,
			labels=graph_labels,
			checkbox_team=checkbox_team,
			checkbox_lines=checkbox_lines,
			rop=graph_rop
		),
		code="""
			for (let team of Object.keys(lines)) {
				lines[team][0].visible = checkbox_team.active.includes(team == 'A' ? 0 : 1) && checkbox_lines.active.includes(0);
				lines[team][1].visible = checkbox_team.active.includes(team == 'A' ? 0 : 1) && checkbox_lines.active.includes(1);
			}
			for (let team of Object.keys(labels)) {
				labels[team].visible = checkbox_team.active.includes(team == 'A' ? 0 : 1) && (checkbox_lines.active.includes(0) || checkbox_lines.active.includes(1));
			}
			for (let key of Object.keys(rop)) {
				rop[key].visible = checkbox_team.active.includes(key.split('_')[0] == 'A' ? 0 : 1) && checkbox_lines.active.includes(2);
			}
		"""
	)
	
	checkbox_team.js_on_change("active", check)
	checkbox_lines.js_on_change("active", check)
	
	graph = row(Inv_graph, column(checkbox_team, checkbox_lines)) # (checkbox_head) Cost_graph, Profit_graph
	show(graph)
	
def savefile():
	global instance
	global tnow
	global policy
	
	if not instance:
		tnow = time.strftime("%d-%h-%Y %H.%M.%S",time.localtime())
		os.mkdir(os.path.abspath(f"./save/{tnow}"))
	instance = len(os.listdir(path_save)) if instance is None else instance
	
	directory = len(os.listdir(f"save/{tnow}"))
	file_policy = "EOQ_Policy" if policy else "No_Policy"
	os.mkdir(os.path.abspath(f"./save/{tnow}/{directory}_{file_policy}"))
	new = xw.Book()
	new.sheets.add()
	for i, sheet in enumerate(["A", "B"]):
		new.sheets[i].name = f"<TEAM_{sheet}> {names[sheet]}"
		Inv[sheet][f"B2:AC{duration+3}"].copy(new.sheets[i][f"B2:AC{duration+3}"])
		new.sheets[i][f"B2:AC{duration+3}"].value = Inv[sheet][f"B2:AC{duration+3}"].value
		
		# with open(os.path.abspath(f"./save/{tnow}/{directory}f_{file_policy}/{sheet}.csv"), "w") as f:
		# 	eoq = [*Inv[sheet]["W5:X5"].value, "", *Inv[sheet]["W6:X6"].value]
		# 	header = ["" if val is None else val for val in Inv[sheet]["B2:U2"].value]
		# 	rows = [["" if val is None else val for val in row] for row in Inv[sheet][f"B3:U{duration+3}"].value]
			
		# 	write = csv.writer(f)
		# 	if policy:
		# 		write.writerow(eoq)
		# 	write.writerow(header)
		# 	write.writerows(rows)
	
	new.save(os.path.abspath(f"./save/{tnow}/{directory}_{file_policy}/data.xlsx"))
	result(os.path.abspath(f"./save/{tnow}/{directory}_{file_policy}/graph.html"))

screen.widgets["saveButton"].config(command=savefile)
screen.widgets["mode1Button"].config(command=lambda: set_game(0))
screen.widgets["mode2Button"].config(command=lambda: set_game(1))
screen.widgets["restartButton"].config(command=restart)

screen.starting()
screen.mainloop()

[CONNECTION[player][0].send("close".encode("UTF-8")) for player in CONNECTION]
print("send_command_close_A")
print("send_command_close_B")

SERVER.close()
