
# Python-Inventory-Game

บริหารจัดการ Carbon และการปล่อยก๊าซเรือนกระจกแบบครบ
วงจร สู่ความยั่งยืนขององกรณ์
โดยการตรวจสอบและทําให้ทราบว่ามีการปล่อยปริมาณ Carbon
ในระบบทั้งหมดเท่าไร รวมถึงทําให้ทราบว่าระบบทั้งหมดมีการ
Offet Carbon หรือ บริหารจัดการได้ประสิทธิภาพเป็นอย่างไร

## Default System

### Develop on

- Python version : 3.10.5
- Windows 11 Home - Version 22H2 - OS build	22631.1906

### .env file

- Setting firewall | RULE_NAME : KU_Inventory_Lab_Open_Port
- Open public | PORT : 50240

### .bat file

The .bat code will request administrator privileges through the UAC of the Windows operating system in order to be used for accessing and opening ports for connection via a public IP.

## Quick Starter

#### TODO : Please install python (Recommended Version 3.10.5+) and pyenv

    $ python -m venv3 env

### For Server

    $ open server.bat (required administrator for open port TCP/UDP)

Example : System print .log important message

    ConnectionGame | passcode_host_server: 159676 (Passcode for Client)
	.
	local_ip: 192.168.1.38 | public_ip: 124.122.115.15 (IP address of host server)
	Server is listening on 192.168.1.38:50240 (Port of host server)

### For Client

    $ open client.bat (required administrator)

Example : System print .log important message

    Enter public IP address: 124.122.115.15
	Enter port: 50240

## Install local for terminal

Create your venv and install requirements.txt

    $ python -m venv3 env
    $ .\env3\Scripts\activate
    $ pip install -r .\requirements.txt

#### Terminal 1 : Server

    $ python server.py

#### Terminal 2 : Client

    $ python client.py
