import mysql.connector
from statistics import NormalDist
import numpy as np
import random


def sign(number):
    number = int(number)
    if number > 0:
        return 1
    elif number < 0:
        return -1
    else:
        return 0

class InventoryDatabase(object):
    def __init__(self):
        #param
        self.period = 0
        #A
        A = {
            "table" : "a",
            "reorder_point" : 14,
            "order_quantity" : 45,
            "leftover" : 0,
            "shortages" : 0,
            "num_order" : 0,
            "unit_sold" : 0,
            "unit_purchase" : 0,
            "fill_rate":0,
            "service_level":0,
            "policy" : False,
            "cash_flow" : {
                            "Revenue" : 0,
                            "Order Cost": 0,
                            "Item Cost": 0,
                            "Holding Cost": 0,
                            "Shortage Cost": 0,
                            "Sales Profit" : 0,
                            "Variable Cost": 0,
                            "Total Cost": 0
                        }
        }
        #B
        B = A.copy()
        B["table"] = 'b'
        B["reorder_point"] = 78
        B["order_quantity"] = 34
        self.INV = { "A" : A.copy(),
                     "B" : B.copy()
                    }
        self.INV_for_reset = self.INV.copy()
        del A,B

        #config
        self.config = {}
        
        self.col_dict = {0: 'period',
                        1: 'demand',
                        2: 'on_order',
                        3: 'arrive',
                        4: 'recieve',
                        5: 'starting_inv',
                        6: 'sold',
                        7: 'shortage',
                        8: 'ending_inv',
                        9: 'order',
                        10: 'eoq_order',
                        11: 'revenue',
                        12: 'item_cost',
                        13: 'order_cost',
                        14: 'holding_cost',
                        15: 'shortage_cost',
                        16: 'sales_profit',
                        17: 'variable_cost'
                        }
        
        self.col_dict_inv = {v: k for k, v in self.col_dict.items()}


        self.excel_column = {
            "Period" : "B",
            "Demand" : "C",
            "On order" : "D",
            "Arrive" : "E",
            "Recieve" : "F",
            "Starting_inv" : "G",
            "Sold" : "H",
            "Shortage" : "I",
            "Ending_inv" : "J",
            "Order" : "L",
            "Eoq order" :"M",
            "Revenue" : "O",
            "Item Cost" : "P",
            "Order Cost" : "Q",
            "Holding Cost" : "R",
            "Shortage Cost" :"S",
            "Sales Profit" : "T",
            "Variable Cost" : "U",
        }

    def database_init(self,database_info):
        self.db = mysql.connector.connect(
            host = database_info['host'],
            port =database_info['port'],
            user = database_info['user'],
            password = database_info['password'],
            database = database_info['database']
    )
        self.cursor = self.db.cursor()
        self.database_name = database_info['database']
    
    def create_new_row(self):
        new_row = {
            "period" : 0,
            "demand" : 0,
            "on_order" : 0,
            "arrive" : 0,
            "recieve" : 0,
            "starting_inv" :0,
            "sold" :0,
            "shortage": 0,
            "ending_inv":0,
            "order":0,
            "eoq_order":0,
            "revenue":0,
            "item_cost":0,
            "order_cost":0,
            "holding_cost":0,
            "shortage_cost":0,
            "sales_profit":0,
            "variable_cost":0
        }
        return new_row
    

    
    def reset_db(self):
        self.cursor.close()
        self.cursor = self.db.cursor()
        self.period = 0
        Tables = ['a','b','config']
        for table in Tables:

            reset = f'''
                        TRUNCATE TABLE {table};
                    '''
            self.cursor.execute(reset)
            self.db.commit()

    # '''
    # RECREATE Data Calculation based on EXCEL formula by using SQL Database
    # '''

    def demand_order_create(self):
        self.period += 1 
        if self.config['sigma'] == 0:
            demand = self.config['mu']
        else:
            demand =  round(NormalDist(mu=5, sigma=2).inv_cdf(random.uniform(0, 1)))
        sql = f'''
                INSERT INTO config (period,demand)
                VALUES ({self.period},{demand});
              '''
        self.cursor.execute(sql)
        self.db.commit()

    def get_current_demand(self):
        current_demand = f'''
            SELECT * FROM config ORDER BY {"period"} DESC 
            LIMIT 1
        '''
        self.cursor.execute(current_demand)
        buffer_data = self.cursor.fetchall()[0]
        return buffer_data[1]

    def get_column(self,column,team):
        get_column = f'''
            SELECT {column} FROM {team}
        '''
        self.cursor.execute(get_column)
        buffer_data = self.cursor.fetchall()
        values = []
        for value in buffer_data:
            values.append(value[0])
        return values

    def get_current_row(self,player):
        select_row_before = f'''
            SELECT * FROM {self.INV[player]['table']} ORDER BY {"period"} DESC 
            LIMIT 1
        '''
        self.cursor.execute(select_row_before)
        buffer_data = self.cursor.fetchall()[0]
        return buffer_data

    def get_all_data(self,player):
        select_all = f'''
            SELECT * FROM {self.INV[player]['table']} ORDER BY {"period"}
        '''
        self.cursor.execute(select_all)
        buffer_data = self.cursor.fetchall()
        return buffer_data

    def create_new_order(self,order,player):
        new_data = self.create_new_row()
        get_demand = f'''
            SELECT demand from config where period = {self.period}
        '''
        self.cursor.execute(get_demand)
        #demand
        new_data['demand'] = self.cursor.fetchall()[0][0]

        new_data['order'] = order

        if self.period == 1:
            new_data["shortage"] = new_data['demand']
            new_data["eoq_order"] = self.INV[player]['order_quantity']
            new_data["order_cost"] = sign(order) * self.config["order_cost"] 
            new_data["shortage_cost"] = (self.config['price']-self.config['item_cost']) * new_data['demand']
            new_data['sales_profit'] = -1 * new_data['order_cost']
            new_data['variable_cost'] = new_data['shortage_cost'] - new_data['sales_profit']  
        else:
            
        #Calculate Excel
            buffer_data = self.get_current_row(player)
        # Arrive
            if buffer_data[self.col_dict_inv["order"]]:
                new_data['arrive'] = self.config['lead_time']
            else:
                if self.period == 2 and buffer_data[self.col_dict_inv["order"]]:
                    new_data['arrive'] = 3
                else:
                    new_data['arrive'] = max(buffer_data[self.col_dict_inv["arrive"]] - 1,0)
        # Recieve
            if new_data['arrive']:
                new_data['recieve'] = 0
            else:
                new_data['recieve'] = buffer_data[self.col_dict_inv["on_order"]] 
        #On order
            if new_data['arrive'] == self.config['lead_time']:
                new_data['on_order'] = buffer_data[self.col_dict_inv["order"]]
            else:
                new_data['on_order'] =   buffer_data[self.col_dict_inv["on_order"]] - new_data['recieve']
        #Starting Inv
            new_data['starting_inv'] = buffer_data[self.col_dict_inv["ending_inv"]] + new_data['recieve']
        #sold 
            new_data['sold'] = min(new_data['demand'],new_data['starting_inv'])
        #Ending Inv
            new_data['ending_inv'] =  new_data['starting_inv'] - new_data['sold'] 
        #Shortage
            new_data['shortage'] = new_data['demand'] - new_data['sold']
        #EOQ_Order
            if new_data['on_order'] + new_data['ending_inv'] <= self.INV[player]['reorder_point']:
                new_data['eoq_order'] = self.INV[player]['order_quantity']
        #Revenue
            new_data['revenue'] = self.config['price'] * new_data['sold']
        #Item cost
            new_data['item_cost'] = self.config['item_cost'] * new_data['recieve']
        #Order cost
            new_data['order_cost'] = sign(new_data['order']) * self.config['order_cost']
        #Holding cost
            new_data['holding_cost'] = self.config['holding_cost'] * ((new_data['starting_inv']+new_data['ending_inv'])/2)
        #Shortage cost
            new_data['shortage_cost'] = (self.config['price']-self.config['item_cost']) * new_data['shortage']
        #Sales profit
            new_data['sales_profit'] = new_data['revenue'] - new_data['item_cost'] - new_data['order_cost'] - new_data['holding_cost']
        #Variable cost
            new_data['variable_cost'] = new_data['order_cost'] + new_data['holding_cost'] + new_data['shortage_cost']


        sql_data_add = f'''
        INSERT INTO {self.database_name}.{self.INV[player]["table"]} (`Period`, `Demand`, `On Order`, `Arrive`, `Recieve`, `Starting Inv`, `Sold`, `Shortage`, `Ending Inv`, `Order_`, `EOQ Order`, `Revenue`, `Item Cost`, `Order Cost`, `Holding Cost`, `Shortage Cost`, `Sales Profit`, `Variable Cost`)
        VALUES {self.period,new_data['demand'],new_data['on_order'],new_data['arrive'],new_data['recieve'],new_data['starting_inv'],new_data['sold'],new_data['shortage'],new_data['ending_inv'],new_data['order'],new_data['eoq_order']
                ,new_data['revenue'],new_data['item_cost'],new_data['order_cost'],new_data['holding_cost'],new_data['shortage_cost'],new_data['sales_profit'],new_data['variable_cost']};
        '''
        self.cursor.execute(sql_data_add)
        self.db.commit()

    
    def update_cashflow_detail(self,player):
        
        #Cashflow of player
        cash_flow = ["Revenue","Order Cost","Item Cost","Holding Cost","Sales Profit","Variable Cost"]
        sum_sql = f'''
            SELECT 
                SUM(`Revenue`) AS total_revenue,
                SUM(`Order Cost`) AS total_order_cost,
                SUM(`Item Cost`) AS total_item_cost,
                SUM(`Holding Cost`) AS total_holding,
                SUM(`Sales Profit`) AS total_sales,
                SUM(`Variable Cost`) AS total_variable,
                SUM(`Shortage Cost`) AS total_shortage
                FROM {self.INV[player]['table']};
            '''
        self.cursor.execute(sum_sql)
        values = self.cursor.fetchall()
        self.INV[player]["cash_flow"]['Revenue'] = int(values[0][0])
        self.INV[player]["cash_flow"]['Order Cost'] = int(values[0][2])
        self.INV[player]["cash_flow"]['Item Cost'] = int(values[0][1])
        self.INV[player]["cash_flow"]['Holding Cost'] = int(values[0][3])
        self.INV[player]["cash_flow"]['Sales Profit'] = int(values[0][4])
        self.INV[player]["cash_flow"]['Variable Cost'] = int(values[0][5])
        self.INV[player]["cash_flow"]['Shortage Cost'] = int(values[0][6])
        self.INV[player]["cash_flow"]['Total Cost'] = int(values[0][1]) + int(values[0][2]) + int(values[0][3]) + int(values[0][6])
        #Total sold purchase and number of order  
        sum_sql = f'''
            SELECT 
                SUM(Shortage) AS total_shortage,
                SUM(Sold) AS total_unit_sold,
                SUM(Recieve) AS total_purchase,
                SUM(Demand) AS total_demand
                FROM {self.INV[player]['table']};
            '''
        self.cursor.execute(sum_sql)
        values = self.cursor.fetchall()
        self.INV[player]["shortages"] = int(values[0][0])
        self.INV[player]["unit_sold"] = int(values[0][1])
        self.INV[player]["unit_purchase"] = int(values[0][2])
        total_demand = int(values[0][3]) 

        #Fill rate and Service Level
        try:
            self.INV[player]["fill_rate"] = total_demand / self.INV[player]["unit_sold"]
        except ZeroDivisionError:
            self.INV[player]["fill_rate"] = 0
        
        if np.sign(self.INV[player]["unit_purchase"]) == 0:
            self.INV[player]["service_level"] = 0
        else:
            self.INV[player]["service_level"] = 1 - sign(self.INV[player]["unit_purchase"] * (self.INV[player]["shortages"]/sign(self.INV[player]["unit_purchase"])))
            
        count_order = f'''
            SELECT COUNT(*) AS count_greater_than_zero
            FROM {self.INV[player]["table"]}
            WHERE Order_ > 0;
        '''
        self.cursor.execute(count_order)
        values = self.cursor.fetchall()
        self.INV[player]["num_order"] = int(values[0][0])

    def reset(self):
        self.INV = self.INV_for_reset.copy()

    def update_result(self,player):

        shortage_cost =(self.config["price"] - self.config["item_cost"]) *(self.config["mu"] * self.config["game_period"] * (1 - self.INV[player]["fill_rate"]))
        holding_cost =  (self.config["holding_cost"] * self.config["game_period"])*((self.INV[player]["order_quantity"]/2) +self.INV[player]["reorder_point"] - self.config["mu"] * self.config["lead_time"])
        order_cost =  (self.config["order_cost"] * self.config["mu"] * self.config["game_period"])/self.INV[player]["order_quantity"]
        fixed_cost = self.config["mu"] * self.config["game_period"] * self.config["item_cost"]
        result = {
            "Order Quantity"            : self.INV[player]["order_quantity"],
            "Reorder Point"             : self.INV[player]["reorder_point"],
            "Safety Stock"              : self.INV[player]["reorder_point"] - self.config["mu"] * self.config["lead_time"],
            "Fill Rate"                 : self.INV[player]["fill_rate"],
            "Service Level"             : self.INV[player]["service_level"],
            "Item Cost"                 : self.config["mu"] * self.config["game_period"] * self.config["item_cost"] ,
            "Order Cost"                : order_cost,
            "Holding Cost"              : holding_cost,
            "Shortage Cost"             : shortage_cost,
            "Total Fixed Cost"          : fixed_cost,
            "Total Variable Cost"       : order_cost+holding_cost+shortage_cost,
            "Total Cost"                : fixed_cost+order_cost+holding_cost+shortage_cost,
            "Total number of demand"    : self.config["mu"] * self.config["game_period"],
            "Total number of orders"    : (self.config["mu"] * self.config["game_period"])/self.INV[player]["order_quantity"],
            "Total number of shortages" : self.config["mu"] * self.config["game_period"] * (1 - self.INV[player]["fill_rate"])
        }
        return result
    
    def create_table(self):
        self.cursor.execute('''
        set SQL_NOTES=0
        ''')
        for player in ["a","b"]:
            create_table_player = f'''
            CREATE TABLE IF NOT EXISTS {self.database_name}.`{player}` (
                `Period` INT NOT NULL,
                `Demand` INT NOT NULL,
                `On Order` INT NOT NULL,
                `Arrive` INT NOT NULL,
                `Recieve` INT NOT NULL,
                `Starting Inv` INT NOT NULL,
                `Sold` INT NOT NULL,
                `Shortage` INT NOT NULL,
                `Ending Inv` INT NOT NULL,
                `Order_` INT NOT NULL,
                `EOQ Order` INT NOT NULL,
                `Revenue` INT NOT NULL,
                `Item Cost` INT NOT NULL,
                `Order Cost` INT NOT NULL,
                `Holding Cost` INT NOT NULL,
                `Shortage Cost` INT NOT NULL,
                `Sales Profit` INT NOT NULL,
                `Variable Cost` INT NOT NULL,
                PRIMARY KEY (`Period`));
            '''
            self.cursor.execute(create_table_player)
        create_config_table = f'''
            CREATE TABLE IF NOT EXISTS {self.database_name}.`config` (
            `period` INT NOT NULL,
            `demand` INT NOT NULL,
            PRIMARY KEY (`period`));
            '''
        self.cursor.execute(create_config_table)
