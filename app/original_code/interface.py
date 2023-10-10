import os
import time
import threading
import xlwings as xw
import tkinter as tk
import tkinter.font
from PIL import Image, ImageTk
from tkinter import ttk
from random import randint
from playsound import playsound

class ScrollableFrame(ttk.Frame):
	def __init__(self, container, *args, **kwargs):
		super().__init__(container, *args, **kwargs)
		self.canvas = tk.Canvas(self)
		#[
		#	self.canvas.create_line((i+1)*12, 10, (i+1)*6, 420)
		#	for i in range(150)
		#]
		self.scrollbar = ttk.Scrollbar(
			self, orient="vertical", command=self.canvas.yview
		)
		self.scrollable_frame = tk.Frame(self.canvas)

		self.scrollable_frame.bind(
			"<Configure>",
			lambda e: self.canvas.config(
				scrollregion=self.canvas.bbox("all")
			)
		)
		self.canvas.create_window((0, 0), window=self.scrollable_frame, anchor="nw")
		self.canvas.config(yscrollcommand=self.scrollbar.set)
		self.canvas.pack(side="left", fill="both", expand=True)
		self.scrollbar.pack(side="right", fill="y")

"""
=======================================================================
=======================================================================

				MAIN SCREEN

=======================================================================
=======================================================================
"""

class Front_screen(tk.Tk):
	def __init__(self):
		super().__init__()
		
		#self.style = ttk.Style()
		#self.style.config('Treeview', rowheight=23)
		#self.style.config('Treeview.Heading', rowheight=23)
		
		self.team = ["A", "B"]
		self.board = ["A", "Main", "B"]
		self.show_parameter = tk.IntVar()
		self.widgets = {
			"Output":{},
			"Parameters":{},
			"Scoreboard":{
				"Name":{}
			},
			"Title":{},
		}
		self.parameters = [
			"Price",
			"Item_cost",
			"Order_cost",
			"Holding_cost",
			"Lead_time",
			"Demand_Distribution",
		]
		
		self.cost = ["Item", "Ordering", "Holding" ,"Shortage"]
		#self.cost = ["Item", "Ordering", "Holding"]
		self.sideColumns = [
			"Day",
			"Demand",
			"OnHand\n(Beginning)",
			"OnHand\n(Ending)",
			"OnOrder",
			"Number\nof\nShortages",
			"Revenue",
			*self.cost,
		]
		self.mainColumns = []
		self.Columns_colour = {key:None for key in self.sideColumns}
		self.Columns_colour["Shortage"] = "gray"
		#self.sideColumns = ["OnHand", "Sold", "Order", "Revenue", *self.cost, "Profit"]
		self.headsize = (len(self.sideColumns), len(self.mainColumns))
		
		self.widgets["board"] = tk.Frame(
			self,
			highlightbackground = "gray",
			highlightthickness = 2,
		)
		self.widgets["Titleboard"] = tk.Frame(self, background="black")
		
		self.lastadd = []
		self.player = dict.fromkeys(self.team)
		self.room = []
		self.policy = False
		
		self.images = {
			"trophy":ImageTk.PhotoImage(Image.open(os.path.abspath("./image/uses/trophy.png"))),
			"tick":ImageTk.PhotoImage(Image.open(os.path.abspath("./image/uses/tick.png"))),
		}
		
		"""
		=======================================================================
		
	waiting screen
		
		=======================================================================
		"""
		
		self.widgets["waiting"] = tk.Label(
			self,
			text=f"waiting for player ...",
		)
		self.font_config(self.widgets["waiting"], size=35)
		
		self.widgets["selectMode"] = tk.Label(
			self,
			text=f"select game mode.",
		)
		self.font_config(self.widgets["selectMode"], size=45)
		
		"""
		=======================================================================
		
	Title
		
		=======================================================================
		"""
		
		self.widgets["Title"]["day"] = tk.Label(
			self.widgets["Titleboard"],
			text="DAY: 0",
			bg="black",
			fg="white",
		)
		self.widgets["Title"]["demand"] = tk.Label(
			self.widgets["Titleboard"],
			text="DEMAND: 00",
			bg="black",
			fg="white",
		)
		
		self.font_config(self.widgets["Title"]["day"], size=30)
		self.font_config(self.widgets["Title"]["demand"], size=30)
		self.widgets["Title"]["day"].grid(row=0, column=0, padx=32)
		self.widgets["Title"]["demand"].grid(row=0, column=1, padx=32)
		
		"""
		=======================================================================
		
	scoreboard
		
		=======================================================================
		"""
		
		self.widgets["Scoreboard"]["log"] = {board:{} for board in self.board}
		self.widgets["Scoreboard"]["Name"] = {
			team:tk.Label(
				self.widgets["board"],
				text=4*" "*i+f"team {team}"+4*" "*(1-i),
				fg = "blue" if i else "red"
			)
			for i, team in enumerate(self.team)
		}
		[
			(
				self.font_config(
					self.widgets["Scoreboard"]["Name"][team],
					size=26,
				),
				self.widgets["Scoreboard"]["Name"][team].grid(
					row = 0,
					column = i*(self.headsize[0]+self.headsize[1]+2),
					columnspan = self.headsize[0],
					#sticky = "e" if i else "w",
					pady = 8
				),
			) for i, team in enumerate(self.team)
		]
		
		self.widgets["Scoreboard"]["head"] = [
			(
				tk.Label(
					self.widgets["board"],
					text = "Cost",
					bg = "pink",
					height = 2,
					width = 36,
					borderwidth = 1,
					relief = "raised",
				) if text==self.cost[0] else None,
				tk.Label(
					self.widgets["board"],
					text = text,
					bg = "gray95" if text == "Day" else "lightgreen" if text=="Revenue" else "pink" if text in self.cost else None,
					fg = "gray35" if text == "Day" else None,
					height = 2 if text in self.cost else 5,
					width = 8,
					borderwidth = 1,
					relief = "raised",
				)
			)
			for text in [*self.sideColumns, *self.mainColumns, *self.sideColumns]
		]
		[
			(
				self.font_config(header[0], size=8) if header[0] else None,
				self.font_config(header[1], size=8),
				header[0].grid(
					row = 1,
					column = i+(i>=self.headsize[0])+(i>=sum(self.headsize)),
					columnspan = len(self.cost),
					pady = 6,
					#padx = ,
				) if header[0] else None,
				header[1].grid(
					row = 1 + (header[1]["text"] in self.cost),
					column = i+(i>=self.headsize[0])+(i>=sum(self.headsize)),
					rowspan = 2 - (header[1]["text"] in self.cost),
					pady = 6,
				),
			)
			for i, header in enumerate(self.widgets["Scoreboard"]["head"])
		]
		
		self.widgets["boardLog"] = ScrollableFrame(self.widgets["board"])
		self.widgets["boardLog"].canvas.config(height=350, width=1220)
		self.widgets["boardLog"].grid(
			row = 3,
			column = 0,
			columnspan = 2*self.headsize[0]+self.headsize[1]+2,
		)
		
		self.widgets["Scoreboard"]["Output"] = [
			tk.Label(
				self.widgets["board"],
				text = "0",
				fg = self.column_color(i),
			)
			for i in 2*self.sideColumns
		]
		[
			(
				self.font_config(score, size=10),
				score.grid(
					row = 4,
					column = i+(self.headsize[1]+2 if i >= self.headsize[0] else 0),
					pady = 10,
				),
			) for i, score in enumerate(self.widgets["Scoreboard"]["Output"])
		]
		"""
		=======================================================================
		
	parameters
		
		=======================================================================
		"""
		
		self.widgets["Parameters"] = {
			param:tk.Label(self, text=f"{param}: ".replace("_"," "), fg="orange")
			for param in self.parameters
		}
		[
			self.font_config(self.widgets["Parameters"][param], size=14)
			for param in self.widgets["Parameters"]
		]
		
		"""
		=======================================================================
		
	total score
		
		=======================================================================
		"""
		
		self.widgets["Total_Profit"] = {
			team:tk.Label(self, text="Sale Profit:"+4*" ") for team in self.team
		}
		[
			self.font_config(self.widgets["Total_Profit"][team], size=20)
			for team in self.widgets["Total_Profit"]
		]
		# self.widgets["Total_Fix"] = {
		# 	team:tk.Label(self, text="Fixed cost:"+4*" ") for team in self.team
		# }
		# [
		# 	self.font_config(self.widgets["Total_Fix"][team], size=22)
		# 	for team in self.widgets["Total_Fix"]
		# ]
		self.widgets["Total_Var"] = {
			team:tk.Label(self, text="Variable Cost:"+4*" ") for team in self.team
		}
		[
			self.font_config(self.widgets["Total_Var"][team], size=20)
			for team in self.widgets["Total_Var"]
		]
		self.widgets["Total_True_Var"] = {
			team:tk.Label(self, text="Actual Variable Cost:"+4*" ") for team in self.team
		}
		[
			self.font_config(self.widgets["Total_True_Var"][team], size=20)
			for team in self.widgets["Total_True_Var"]
		]
		self.widgets["signal"] = {team:tk.Label(self) for team in self.team}
		"""
		=======================================================================
		
	spacing
		
		=======================================================================
		"""
		
		[
			tk.Label(self.widgets["board"]).grid(row=0, column=i, padx=10)
			for i in (self.headsize[0], sum(self.headsize)+1)
		]
		[
			tk.Label(
				self.widgets["boardLog"].scrollable_frame,
			).grid(row=0, column=i, padx=10)
			for i in (self.headsize[0], sum(self.headsize)+1)
		]
		
		# for i, board in enumerate(self.board):
		# 	columns = self.mainColumns if board=="Main" else self.sideColumns
		# 	self.widgets["Scoreboard"][board] = ttk.Treeview(
		# 		self.widgets["board"],
		# 		column = columns,
		# 		show = "headings"
		# 	)
		# 	[
		# 		(
		# 		 self.widgets["Scoreboard"][board].heading(i,	text=i),
		# 			self.widgets["Scoreboard"][board].column(
		# 				i,
		# 				minwidth	=	0,
		# 				width	=	60,
		# 				stretch	=	tk.NO,
		# 				anchor=tk.CENTER,
		# 			)
		# 		)
		# 		for i in columns
		# 	]
			
		# 	self.widgets["Scoreboard"][board].grid(row=0, column=2*i,)
		
		# [
		# 	tk.Label(self.widgets["board"], text=" "*48).grid(row=0, column=i)
		# 	for i in [1,3]
		# ]
		
		"""
		=======================================================================
		
	buttons
		
		=======================================================================
		"""
		
		self.widgets["nextButton"] = tk.Button(self, text = "Next", width=6)
		self.widgets["skipButton"] = tk.Button(self, text = ">>", width=1)
		self.widgets["restartButton"] = tk.Button(self, text = "Restart", width=6)
		self.widgets["saveButton"] = tk.Button(self, text = "Save", width=6)
		
		self.widgets["mode1Button"] = tk.Button(self, text="Player vs Player", width=16, command=lambda: self.set_policy(False))
		self.widgets["mode2Button"] = tk.Button(self, text="Player vs EOQ", width=16, command=lambda: self.set_policy(True))
		
		self.widgets["showParameterButton"] = tk.Checkbutton(
			self,
			text = "Show parameters",
			variable = self.show_parameter,
			command = lambda: self.show_parameters(self.show_parameter),
		)
		
		self.font_config(self.widgets["nextButton"], size=16)
		self.font_config(self.widgets["skipButton"], size=16)
		self.font_config(self.widgets["restartButton"], size=16)
		self.font_config(self.widgets["showParameterButton"], size=16)
		
		self.font_config(self.widgets["mode1Button"], size=16)
		self.font_config(self.widgets["mode2Button"], size=16)
		
	def reset(self):
		self.scrollto(0)
		self.lastadd = []
		for board in self.widgets["Scoreboard"]["log"]:
			for i in self.widgets["Scoreboard"]["log"][board]:
				for j in self.widgets["Scoreboard"]["log"][board][i]:
					j.destroy()
		[self.widgets["Total_Profit"][team].config(text="Sale Profit:"+4*" ") for team in self.widgets["Total_Profit"]]
		# [self.widgets["Total_Fix"][team].config(text="Fixed Cost:"+4*" ") for team in self.widgets["Total_Fix"]]
		[self.widgets["Total_Var"][team].config(text="Variable Cost:"+4*" ") for team in self.widgets["Total_Var"]]


		self.widgets["Scoreboard"]["log"] = {board:{} for board in self.board}
		[out.config(text="0") for out in self.widgets["Scoreboard"]["Output"]]
		self.widgets["Title"]["day"].config(text="DAY: 0")
		self.widgets["Title"]["demand"].config(text="DEMAND: 00")
		self.initialscreen()
	
	def initialscreen(self):
		[
			widget.place_forget()
			for widget in self.winfo_children()
		]
		self.widgets["selectMode"].place(relx=.5, rely=.4, anchor=tk.CENTER)
		self.widgets["mode1Button"].place(relx=.25, rely=.6, anchor=tk.W)
		self.widgets["mode2Button"].place(relx=.75, rely=.6, anchor=tk.E)
	
	def mainscreen(self):
		[
			widget.place_forget()
			for widget in self.winfo_children()
		]
		self.widgets["saveButton"].place(relx=.5, rely=.85, anchor=tk.CENTER)
		
		self.widgets["board"].place(relx=.5, rely=.4375, anchor=tk.CENTER)
		self.widgets["Titleboard"].place(relx=.5, rely=.0875, anchor=tk.CENTER)
		self.widgets["nextButton"].place(relx=.375, rely=.85, anchor=tk.CENTER)
		self.widgets["skipButton"].place(relx=.41875, rely=.85, anchor=tk.CENTER) if self.policy else None
		self.widgets["restartButton"].place(relx=.625, rely=.85, anchor=tk.CENTER)
		self.widgets["showParameterButton"].place(relx=.5, rely=.9, anchor=tk.CENTER)
		[
			(
				self.widgets["Total_Profit"][team].place(
					relx=.2+.6*i,
					rely=.8375,
					anchor=tk.CENTER,
				),
				# self.widgets["Total_Fix"][team].place(
				# 	relx=.2+.6*i,
				# 	rely=.925,
				# 	anchor=tk.CENTER,
				# ),
				self.widgets["Total_Var"][team].place(
					relx=.2+.6*i,
					rely=.9,
					anchor=tk.CENTER,
				),
				self.widgets["signal"][team].place(
					relx=.05+.9*i,
					rely=.875,
					anchor=tk.CENTER,
				)
			)
			for i, team in enumerate(self.widgets["Total_Profit"])
		]
		
		#self.widgets["logButton"].place(relx=.5, rely=.975, anchor=tk.CENTER)
	
	def waitingscreen(self):
		[
			widget.place_forget()
			for widget in self.winfo_children()
		]
		self.widgets["waiting"].place(relx=.5, rely=.475, anchor=tk.CENTER)
	
	
	
	def edit_score(self, period, *column, **val):
		for i, col in enumerate(column):
			colnum = self.sideColumns.index(col)
			for title in val:
				self.widgets["Scoreboard"]["log"][title][period][colnum].config(
					text = val[title][i]
				)
	
	def set_total(self, **val):
		[
			self.widgets["Total_Profit"][team].config(
				text=f"Sale Profit: $ {val['profit'][i]}",
				fg = "forestgreen" if val['profit'][i]>0 else "red2",
			) for i, team in enumerate(self.widgets["Total_Profit"])
		]
		# [
		# 	self.widgets["Total_Fix"][team].config(
		# 		text=f"Fixed cost: $ {val['fix'][i]}",
		# 		fg = "forestgreen" if val['fix'][i]>0 else "red2",
		# 	) for i, team in enumerate(self.widgets["Total_Fix"])
		# ]
		[
			self.widgets["Total_Var"][team].config(
				text=f"Variable Cost: $ {val['var'][i]}",
				fg = "forestgreen" if val['var'][i]>0 else "red2",
			) for i, team in enumerate(self.widgets["Total_Var"])
		]
	
	# def set_leftover(self, *val):
	# 	[
	# 		self.widgets["Leftover"][team].config(
	# 			text=f"Profit: {val[i]}\nLeftover: {val[i+2]} units",
	# 			fg = "forestgreen" if val[i]>0 else "red2",
	# 		) for i, team in enumerate(self.widgets["Total_Profit"])
	# 	]
	
	def receive_order(self, team):
		self.widgets["signal"][team].config(image=self.images["tick"])
	
	def clear_order(self):
		[self.widgets["signal"][team].config(image="") for team in self.team]
	
	def column_color(self, column):
		color = {key:None for key in self.sideColumns}
		for key, clr in zip(
			["Day", "Revenue", *self.cost, "Shortage"],
			["azure4", "forestgreen", *["red2" for _ in self.cost], "lightcoral"],
		):
			color[key] = clr
		return color[column]
	
	def scrollto(self, num):
		self.widgets["boardLog"].canvas.yview_moveto(num)
	
	def font_config(self, widget, **config):
		font = tk.font.Font(font=widget).actual()
		font = {key:config[key] if key in config else font[key] for key in font}
		widget.config(font = tuple(font[key] for key in ["family", "size"]))
	
	def team_name(self, **name):
		[
			self.widgets["Scoreboard"]["Name"][team].config(
				text=32*" "*i+f"TEAM {team}: {name[team]}"+32*" "*(1-i),
			)
			for i, team in enumerate(name)
		]
	
	def set_parameters(self, **val):
		[
			self.widgets["Parameters"][param].config(
				text = f"{param}: {val[param]}".replace("_"," "),
			) for param in val
		]
	
	def show_parameters(self, toggle):
		[
			self.widgets["Parameters"][param].place(
				relx=(i+1)/(len(self.parameters)+1)-.05,
				rely=.025,
				anchor=tk.W,
			) if toggle.get() else self.widgets["Parameters"][param].place_forget()
			for i, param in enumerate(self.widgets["Parameters"])
		]
	
	def connecting(self, player, *_, check=0):
		if check < len(self.team):
			if not self.player[self.team[check]]:

				self.player[self.team[check]] = player
				self.room = self.room + [player]
			else:
				self.connecting(player, *_, check=check+1)
			
		self.update()
	
	def starting(self):
		if len(self.room) >= len(self.team):
			self.team_name(**self.player)
			self.widgets["waiting"].config(
				text = "game starting...",
			)
			self.update()
			time.sleep(1)
			self.initialscreen()
			
	
	def game_over(self, **val):
		[
			self.widgets["Total_True_Var"][team].place(
				relx=.2+.6*i,
				rely=.9625,
				anchor=tk.CENTER,
			)
			for i, team in enumerate(self.widgets["Total_True_Var"])
		]
		[
			self.widgets["Total_Var"][team].config(
				text=f"Variable Cost: {val[f'{team}_game_var']} ({val[f'{team}_game_cycle']} cycles)",
				fg = "red2",
			)
			for team in self.widgets["Total_Var"]
		]
		[
			self.widgets["Total_True_Var"][team].config(
				text=f"Actual Variable Cost: {val[f'{team}_true_var']} ({val[f'{team}_true_cycle']} cycles)",
				fg = "lightcoral"
			)
			for team in self.widgets["Total_True_Var"]
		]
	
	def set(self ,resolution = "1800x900"):
		self.geometry(resolution)
		self.waitingscreen()
		self.update()

"""
=======================================================================
=======================================================================

				USER GUI

=======================================================================
=======================================================================
"""

class User_GUI(tk.Tk):
	def __init__(self):
		super().__init__()
		self.name = None
		self.policy = False
		self.initial = True
		self.widgets = {
			"Title":{}
		}
		self.output = {
			"period":0,
			"demand":0,
			"onhand":0,
			"onorder":0,
			"arrive":0,
			"receive":0,
			"sold":0,
			"Shortage":0,
			"profits":0,
			"varcost":0,
		}
		self.order = self.order_prev = 0
		self.EOQ = 0
		self.ROP = 0
		self.onorder = False
		
		self.widgets["Titleboard"] = tk.Frame(self, background="black")
		self.widgets["teamName"] = tk.Label(self, text="Enter team name:")
		self.widgets["ask"] = tk.Label(self, text="Enter your initial stock to begin:")
		
		self.font_config(self.widgets["teamName"], size=30)
		self.font_config(self.widgets["ask"], size=30)
		
		self.widgets["waiting"] = tk.Label(
			self,
			text=f"waiting for other players ...",
		)
		
		self.sequence = {
			"stock":{
				"cash":[],
				"lost":[],
				"tv":[],
				"box":[],
			},
			"deli":[]
		}
		
		self.font_config(self.widgets["waiting"], size=40)
		self.widget_position = {
			"nameBox":{"relx":.65, "rely":.5, "anchor":tk.CENTER},
			"orderAmount":{"relx":.525, "rely":.75, "anchor":tk.W},
			"EOQAmount":{"relx":.35, "rely":.75, "anchor":tk.W},
			"ROPAmount":{"relx":.725, "rely":.75, "anchor":tk.W},
			
			"teamName":{"relx":.4, "rely":.5, "anchor":tk.E},
			
			"confirmButton":{"relx":.875, "rely":.75, "anchor":tk.CENTER},
			"yesButton":{"relx":.875, "rely":.75, "anchor":tk.CENTER},
			"noButton":{"relx":.95, "rely":.75, "anchor":tk.CENTER},
			"cancelButton":{"relx":.95, "rely":.75, "anchor":tk.CENTER},
			
			"loginButton":{"relx":.875, "rely":.5, "anchor":tk.CENTER},
			
			"ask":{"relx":.1, "rely":.75, "anchor":tk.W},
			"waiting":{"relx":.5, "rely":.475, "anchor":tk.CENTER},
			
			"onhand":{"relx":.075, "rely":.15, "anchor":tk.NW},
			"onorder":{"relx":.575, "rely":.15, "anchor":tk.NW},
			"profits":{"relx":.1, "rely":.875, "anchor":tk.W},
			"fixcost":{},
			"varcost":{"relx":.9, "rely":.875, "anchor":tk.E},
		}
		self.images = {
			"box":[
				ImageTk.PhotoImage(Image.open(os.path.abspath("./image/uses/"+img)))
				for img in os.listdir(os.path.abspath("./image/uses"))
				if img.split("_")[0] == "box"
			],
			"cash":[
				ImageTk.PhotoImage(Image.open(os.path.abspath("./image/uses/"+img)))
				for img in os.listdir(os.path.abspath("./image/uses"))
				if img.split("_")[0] == "cash"
			],
			"tv":[
				ImageTk.PhotoImage(Image.open(os.path.abspath("./image/uses/"+img)))
				for img in os.listdir(os.path.abspath("./image/uses"))
				if img.split("_")[0] == "tv"
			],
			"cross":ImageTk.PhotoImage(Image.open(os.path.abspath("./image/uses/cross.png"))),
			"truck":ImageTk.PhotoImage(Image.open(os.path.abspath("./image/uses/truck.png"))),
			"warehouse":ImageTk.PhotoImage(Image.open(os.path.abspath("./image/uses/warehouse.png"))),
		}

		# self.images = {
		#	items:[
		#	ImageTk.PhotoImage(img)
		#	for img in images[items]
		#	] for items in images
		# }
		
		self.stock_row = 5
		self.stock_column = 6
		self.deli_row = 5
		self.deli_column = 6
		
		self.font_config(self.widgets["waiting"], size=35)
		
		"""
		=======================================================================
		
	Title
		
		=======================================================================
		"""
		
		self.widgets["Title"]["day"] = tk.Label(
			self.widgets["Titleboard"],
			text="DAY: 0",
			bg="black",
			fg="white",
		)
		self.widgets["Title"]["demand"] = tk.Label(
			self.widgets["Titleboard"],
			text="DEMAND: 00",
			bg="black",
			fg="white",
		)
		self.font_config(self.widgets["Title"]["day"], size=35)
		self.font_config(self.widgets["Title"]["demand"], size=35)
		
		self.widgets["Title"]["day"].grid(row=0, column=0, padx=32)
		self.widgets["Title"]["demand"].grid(row=0, column=1, padx=32)
		
		"""
		=======================================================================
		
	Scoreboard
		
		=======================================================================
		"""
		self.widgets["frame_title"] = {
			"onhand":tk.Frame(self),
			"onorder":tk.Frame(self),
		}
		
		self.widgets["onhand_image"] = tk.Label(self.widgets["frame_title"]["onhand"])
		self.widgets["onhand"] = tk.Label(self.widgets["frame_title"]["onhand"])
		self.widgets["onorder_image"] = tk.Label(self.widgets["frame_title"]["onorder"])
		self.widgets["onorder"] = tk.Label(self.widgets["frame_title"]["onorder"])
		
		self.widgets["onhand_image"].grid(row=0, column=0)
		self.widgets["onhand"].grid(row=0, column=1)
		self.widgets["onorder_image"].grid(row=0, column=0)
		self.widgets["onorder"].grid(row=0, column=1)
		
		self.widgets["Total_Profit"] = tk.Label(self, fg="forestgreen")
		self.widgets["Total_Var"] = tk.Label(self, fg="red2")
		
		self.font_config(self.widgets["onhand"], size=25)
		self.font_config(self.widgets["onorder"], size=25)
		self.font_config(self.widgets["Total_Profit"], size=30)
		self.font_config(self.widgets["Total_Var"], size=30)
		
		self.widgets["frame"] = {
			"stock":tk.Frame(self),
			"deli":tk.Frame(self),
		}
		self.widgets["inframe"] = {
			"stock":[
				tk.Label(self.widgets["frame"]["stock"])
				for i in range(self.stock_row*self.stock_column)
			],
			"deli":[
				tk.Label(self.widgets["frame"]["deli"])
				for i in range(self.deli_row*self.deli_column)
			],
		}

		[
			items.grid(**self.grid_of(i, self.stock_column),)
			for i, items in enumerate(self.widgets["inframe"]["stock"])
		]
		[
			items.grid(**self.grid_of(i, self.stock_column),)
			for i, items in enumerate(self.widgets["inframe"]["deli"])
		]
		"""
		=======================================================================
		
	Entry
		
		=======================================================================
		"""
		
		self.widgets["nameBox"] = tk.Entry(self)
		self.widgets["orderAmount"] = tk.Entry(self, width=4)
		self.widgets["EOQAmount"] = tk.Entry(self, width=4)
		self.widgets["ROPAmount"] = tk.Entry(self, width=4)
		
		self.widgets["nameBox"].config(
			validate="key",
			validatecommand=(
				self.register(lambda val: (len(val)<=8)*all([
					not str in r":\/*[]"
					for str in val
				]) if len(val) else True),
				"%P",
			),
		)
		self.widgets["orderAmount"].config(
			validate="key",
			validatecommand=(
				self.register(lambda val: (len(val)<=3)*all([
					str in "0123456789"
					for str in val
				]) if len(val) else True),
				"%P",
			),
		)
		
		self.widgets["EOQAmount"].config(
			validate="key",
			validatecommand=(
				self.register(lambda val: (len(val)<=3)*all([
					str in "0123456789"
					for str in val
				]) if len(val) else True),
				"%P"
			),
		)
		self.widgets["ROPAmount"].config(
			validate="key",
			validatecommand=(
				self.register(lambda val: (len(val)<=3)*all([
					str in "0123456789"
					for str in val
				]) if len(val) else True),
				"%P"
			),
		)
		
		self.font_config(self.widgets["nameBox"], size=30)
		self.font_config(self.widgets["orderAmount"], size=30)
		self.font_config(self.widgets["EOQAmount"], size=30)
		self.font_config(self.widgets["ROPAmount"], size=30)
		"""
		=======================================================================
		
	Button
		
		=======================================================================
		"""
		self.widgets["yesButton"] = tk.Button(
			self,
			text = "Yes",
			command = self.make_order,
		)
		self.widgets["noButton"] = tk.Button(
			self,
			text = "No",
			# command = self.make_no_order,mode1Button
		)
		
		self.widgets["confirmButton"] = tk.Button(
			self,
			text = "Confirm",
			# command = self.confirm_order,
		)
		
		self.widgets["cancelButton"] = tk.Button(
			self,
			text = "Back",
			command = self.cancel_order,
		)

		self.widgets["loginButton"] = tk.Button(
			self,
			text = "Log In",
			#command = self.connecting,
		)
	
	def mainscreen(self):
		[
			widget.place_forget()
			for widget in self.winfo_children()
		]
		self.widgets["Titleboard"].place(relx=.5, rely=.1, anchor=tk.CENTER)
		
		if self.policy:
			self.widgets["frame"]["stock"].place(relx=.075, rely=.25, anchor=tk.NW)
			self.widgets["frame"]["deli"].place(relx=.575, rely=.25, anchor=tk.NW)
			
			self.widgets["frame_title"]["onhand"].place(**self.widget_position["onhand"])
			self.widgets["frame_title"]["onorder"].place(**self.widget_position["onorder"])
			self.widgets["Total_Profit"].place(**self.widget_position["profits"])
			self.widgets["Total_Var"].place(**self.widget_position["varcost"])
			
			self.widgets["EOQAmount"].place(**self.widget_position["EOQAmount"])
			self.widgets["ROPAmount"].place(**self.widget_position["ROPAmount"])
			self.widgets["confirmButton"].place(**self.widget_position["confirmButton"])
			
			self.widgets["ask"].config(text="Order Quantities"+24*" "+"Reorder point")
			self.widgets["ask"].place(**self.widget_position["ask"])
		else:
			self.widgets["frame"]["stock"].place(relx=.075, rely=.25, anchor=tk.NW)
			self.widgets["frame"]["deli"].place(relx=.575, rely=.25, anchor=tk.NW)
			
			self.widgets["frame_title"]["onhand"].place(**self.widget_position["onhand"])
			self.widgets["frame_title"]["onorder"].place(**self.widget_position["onorder"])
			self.widgets["Total_Profit"].place(**self.widget_position["profits"])
			self.widgets["Total_Var"].place(**self.widget_position["varcost"])
			
			self.widgets["orderAmount"].place(**self.widget_position["orderAmount"])
			self.widgets["confirmButton"].place(**self.widget_position["confirmButton"])
			
			self.widgets["ask"].place(**self.widget_position["ask"])
	
	def waitingscreen(self):
		self.name = self.widgets["nameBox"].get()
		[
			widget.place_forget()
			for widget in self.winfo_children()
		]
		self.widgets["waiting"].place(**self.widget_position["waiting"])
	
	def loginscreen(self):
		[
			widget.place_forget()
			for widget in self.winfo_children()
		]
		self.widgets["teamName"].place(**self.widget_position["teamName"])
		self.widgets["nameBox"].place(**self.widget_position["nameBox"])
		self.widgets["loginButton"].place(**self.widget_position["loginButton"])
	
	def make_order(self):
		self.widgets["yesButton"].place_forget()
		self.widgets["noButton"].place_forget()
		
		self.widgets["ask"].config(text="Please enter the order Quantity:")
		self.widgets["orderAmount"].place(**self.widget_position["orderAmount"])
		self.widgets["confirmButton"].place(**self.widget_position["confirmButton"])
		self.widgets["cancelButton"].place(**self.widget_position["cancelButton"])
		
		self.widgets["orderAmount"].delete(0, tk.END)
		self.widgets["orderAmount"].insert(0, self.order_prev) if self.order_prev else None
	
	def make_no_order(self):
		self.order = 0
		self.widgets["yesButton"].place_forget()
		self.widgets["noButton"].place_forget()
		self.widgets["ask"].config(text="You have not pressed an order.")
	
	def cancel_order(self):
		self.widgets["orderAmount"].place_forget()
		self.widgets["confirmButton"].place_forget()
		self.widgets["cancelButton"].place_forget()
		
		self.widgets["ask"].config(text="Do you want to press an order? :")
		self.widgets["yesButton"].place(**self.widget_position["yesButton"])
		self.widgets["noButton"].place(**self.widget_position["noButton"])
	
	def confirm_order(self):
		if self.policy:
			self.EOQ = int(self.widgets["EOQAmount"].get())
			self.ROP = int(self.widgets["ROPAmount"].get())
			self.widgets["ask"].config(text=f"You'll press an order of {self.EOQ} when your inventory position is at {self.ROP}.")
			
			self.widgets["confirmButton"].place_forget()
			self.widgets["EOQAmount"].place_forget()
			self.widgets["ROPAmount"].place_forget()
		else:
			self.order = self.order_prev = int(self.widgets["orderAmount"].get())
			self.widgets["ask"].config(text=f"You have pressed an order of {self.order} televisions.")
			
			self.widgets["orderAmount"].place_forget()
			self.widgets["confirmButton"].place_forget()
			self.widgets["cancelButton"].place_forget()
	
	def updateimage(self):
		[
			items.config(image="") for i, items in enumerate(self.widgets["inframe"]["stock"])
			if i >= len(self.sequence["stock"]["cash"] + self.sequence["stock"]["tv"] + self.sequence["stock"]["box"])
		]
		[
			items.config(image="") for i, items in enumerate(self.widgets["inframe"]["deli"])
			if i >= len(self.sequence["deli"])
		]
		[
			self.widgets["inframe"]["stock"][i].config(image=self.images["cash"][img])
			for i, img in enumerate(self.sequence["stock"]["cash"]) if i < self.stock_row*self.stock_column
		]
		[
			self.widgets["inframe"]["stock"][
				i + len(self.sequence["stock"]["cash"])
			].config(image=self.images["cross"])
			for i, img in enumerate(self.sequence["stock"]["lost"]) if i + len(self.sequence["stock"]["cash"]) < self.stock_row*self.stock_column
		]
		[
			self.widgets["inframe"]["stock"][
				i + len(self.sequence["stock"]["cash"])
			].config(image=self.images["tv"][img])
			for i, img in enumerate(self.sequence["stock"]["tv"]) if i + len(self.sequence["stock"]["cash"]) < self.stock_row*self.stock_column
		]
		[
			self.widgets["inframe"]["stock"][
				i + len(self.sequence["stock"]["cash"] + self.sequence["stock"]["tv"])
			].config(image=self.images["box"][img])
			for i, img in enumerate(self.sequence["stock"]["box"]) if i + len(self.sequence["stock"]["cash"] + self.sequence["stock"]["tv"]) < self.stock_row*self.stock_column
		]
		[
			self.widgets["inframe"]["deli"][i].config(image=self.images["box"][img])
			for i, img in enumerate(self.sequence["deli"]) if i < self.stock_row*self.stock_column
		]
	
	def updatestock(self, skip=0):
		
		last_deli = self.sequence["deli"][:]
		self.sequence["stock"]["box"] = [1 for _ in range(int(self.output["receive"]))] if self.initial else self.sequence["deli"][:int(self.output["receive"])]
		self.sequence["deli"] = self.sequence["deli"] if self.sequence["deli"] and self.output["onorder"] else [1 for _ in range(int(self.output["onorder"]))]
		
		if not skip:
			self.updateimage()
			try:
				playsound(os.path.abspath("./sound/zapsplat_foley_cardboard_box_small_empty_set_down_or_drop_on_hard_ground_006_85860.mp3"), block=False) if self.sequence["stock"]["box"] else None
				playsound(os.path.abspath("./sound/zapsplat_household_wicker_basket_hamper_set_down_004_85827.mp3"), block=False) if self.sequence["deli"]*(not last_deli) else None
			except:
				print("sound does not play error raised")
			time.sleep(.5)
		
		self.sequence["stock"]["tv"] = [*self.sequence["stock"]["tv"], *[3 for _ in range(int(self.output["receive"]))]]
		self.sequence["stock"]["box"] = []
		
		if not skip:
			self.updateimage()
			try:
				playsound(os.path.abspath("./sound/zapsplat_foley_notepad_page_thin_paper_a4_ring_binded_rip_tear_from_pad_fast_001_33418.mp3"), block=False) if self.output["receive"] else None
			except:
				print("sound does not play error raised")
			time.sleep(1)
		
		self.sequence["stock"]["cash"] = [self.sequence["stock"]["tv"].pop(0) for i in range(int(self.output["sold"])) if len(self.sequence["stock"]["tv"])]
		
		self.updateimage() if not skip else None
		try:
			playsound(os.path.abspath("./sound/Blastwave_FX_CashRegister_S08IN.92.mp3"), block=False) if self.sequence["stock"]["cash"] else None
		except:
			print("sound does not play error raised")
		time.sleep(.25) if not skip else None
		
		self.sequence["stock"]["lost"] = [1 for _ in range(int(self.output["Shortage"]))]
		
		self.updateimage()
		try:
			playsound(os.path.abspath("./sound/zapsplat_multimedia_alert_error_003_26394.mp3"), block=False) if self.sequence["stock"]["lost"] else None
		except:
			print("sound does not play error raised")
		time.sleep(.2 if skip else 1.75)
		
		self.sequence["stock"]["cash"] = []
		self.sequence["stock"]["lost"] = []
		self.updateimage()
		
		# self.sequence["stock"]["box"] = [randint(0,3) for _ in range(int(self.output["receive"]))] if self.initial else self.sequence["deli"][:int(self.output["receive"])]
		# self.sequence["deli"] = self.sequence["deli"] if self.sequence["deli"] and self.output["onorder"] else [randint(0,3) for _ in range(int(self.output["onorder"]))]
		# self.updateimage()
		
		# time.sleep(.5)
		
		# self.sequence["stock"]["tv"] = [*self.sequence["stock"]["tv"], *[self.sequence["stock"]["box"].pop(0) for _ in range(int(self.output["receive"]))]]
		# self.updateimage()
		
		# time.sleep(1)
		
		# self.sequence["stock"]["cash"] = [self.sequence["stock"]["tv"].pop(0) for i in range(int(self.output["sold"]))]
		# self.updateimage()
		
		# time.sleep(2)
		
		# self.sequence["stock"]["cash"] = []
		# self.updateimage()
		
		while len(self.sequence["stock"]["tv"]) > int(self.output["onhand"]):
			self.sequence["stock"]["tv"].pop()
		
		while len(self.sequence["stock"]["tv"]) < int(self.output["onhand"]):
			self.sequence["stock"]["tv"] = self.sequence["stock"]["tv"]+[3]
		
		self.updateimage()
		
		if not skip:
			self.widgets["Title"]["day"]["text"] = f"END OF DAY"
			self.widgets["Title"]["demand"]["text"] = self.output['period']
	
	def next_turn(self, output, skip=0):
		self.output = output
		
		self.widgets["Title"]["day"]["text"] = f"DAY: {self.output['period']}"
		self.widgets["Title"]["demand"]["text"] = f"DEMAND: {int(self.output['demand'])}"
		
		if not self.policy:
			self.widgets["orderAmount"].place_forget()
			self.widgets["confirmButton"].place_forget()
			self.widgets["cancelButton"].place_forget()
			self.widgets["ask"].config(text="Do you want to press the order? :")
			self.widgets["yesButton"].place(**self.widget_position["yesButton"])
			self.widgets["noButton"].place(**self.widget_position["noButton"])
		self.order = 0
		self.onorder = bool(self.output["onorder"])
		self.widgets["onhand_image"].config(image=self.images["warehouse"])
		self.widgets["onorder_image"].config(image=self.images["truck"])
		self.widgets["onhand"].config(text=f"on hand ({int(self.output['onhand'])})")
		self.widgets["onorder"].config(text=f"on order ({int(self.output['onorder'])})    {'arrive in: '+str(int(self.output['arrive']))+' day(s)' if self.output['arrive'] else ''}")
		self.widgets["Total_Profit"].config(text=f"Sale Profit: $ {int(self.output['profits'])}", fg="forestgreen" if self.output['profits'] >= 0 else "red2")
		self.widgets["Total_Var"].config(text=f"Variable Cost: $ {int(self.output['varcost'])}", fg="forestgreen" if self.output['varcost'] >= 0 else "red2")
		self.updatestock(skip)
		self.initial = False
	
	def reset(self):
		self.initial = True
		self.output = {
			"period":0,
			"demand":0,
			"onhand":0,
			"onorder":0,
			"arrive":0,
			"receive":0,
			"sold":0,
			"Shortage":0,
			"profits":0,
			"varcost":0,
		}
		self.sequence = {
			"stock":{
				"cash":[],
				"lost":[],
				"tv":[],
				"box":[],
			},
			"deli":[]
		}
		self.widgets["onhand_image"].config(image="")
		self.widgets["onorder_image"].config(image="")
		self.widgets["onhand"].config(text="")
		self.widgets["onorder"].config(text="")
		self.widgets["Total_Profit"].config(text="")
		self.widgets["Total_Var"].config(text="")
		[items.config(image="") for items in self.widgets["inframe"]["stock"]]
		[items.config(image="") for items in self.widgets["inframe"]["deli"]]
		self.widgets["ask"].config(text="Enter your initial stock to begin:")
		
		self.widgets["Title"]["day"].config(text="DAY: 0")
		self.widgets["Title"]["demand"].config(text="DEMAND: 00")
		
	def grid_of(self, location, column):
		return {"row":int(location/column), "column":int(location%column)}
	
	def font_config(self, widget, **config):
		font = tk.font.Font(font=widget).actual()
		font = {key:config[key] if key in config else font[key] for key in font}
		widget.config(font = tuple(font[key] for key in ["family", "size"]))
	
	def set(self ,resolution = "1340x700"): #1080x600
		self.geometry(resolution)
		self.loginscreen()
		self.update()