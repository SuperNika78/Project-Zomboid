from flask import Flask, render_template, request, redirect
import sqlite3
from dotenv import load_dotenv
import os
import subprocess
import re
from. utils import auth_required

app = Flask(__name__)

# Define Database Connection
_DATABASE = "/home/pzuser/Zomboid/Saves/Multiplayer/servertest/players.db"

def get_db_connection():
    conn = sqlite3.connect(_DATABASE)
    conn.row_factory = sqlite3.Row
    return conn

# Routing
@app.route('/')
@auth_required
def index():
    return render_template('index.html', title='Project Zomboid')

@app.route('/server/uptime')
def get_uptime():
    uptime = getServiceUptime('zomboid')  # Replace 'zomboid' with your service name
    return {"uptime": uptime}, 200  # Return JSON with the uptime


@app.route('/server')
@auth_required
def admin():
    server_info = {
        "ip": request.host.split(':')[0],
        "port": 16261,
        "running": isServerActive(),
        "player_count": getPlayerList()[0],
        "uptime":getServiceUptime('zomboid')
    }
    return render_template('server.html', server = server_info)

@app.post('/server/<action>')
@auth_required
def start(action):
    success = serverSystemd(action, 'zomboid')
    response = {
        "success": success,
        "action": action,
        "running": isServerActive(),
        "player_count": getPlayerList()[0],
        "uptime":getServiceUptime('zomboid')
    }
    return response, 200

def getServiceUptime(service_name: str) -> str:
    try:
        # Run the systemctl status command
        result = subprocess.run(
            ['systemctl', 'status', service_name],
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=True
        )
        
        if result.returncode != 0:
            return "-"
        
        # Search for the uptime in the command output
        match = re.search(r'.*; (\d+.*) ago', result.stdout)
        if match:
            return match.group(1)  # Extract the uptime string
        else:
            return f"Could not determine uptime for {service_name}."

    except Exception as e:
        return f"Error: {str(e)}"

# Function to Access Database or Systen Services
def getPlayerList() -> int:
    conn = get_db_connection()
    total_player = conn.execute("SELECT COUNT() FROM networkPlayers").fetchone()
    conn.close()
    return total_player

# Function to Run Syetemctl to Control Zomboid Server (Start, Restart, Stop, Is-Active)
def serverSystemd(action: str, service_name: str):
    action_list = ['is-active', 'start', 'stop', 'restart']
    if action in action_list:
        try:
            result = subprocess.run(
                ['systemctl', action, service_name],
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                text=True
            )
            if action == 'is-active':
                return result.stdout.strip() == "active"
            elif action == 'start':
                return isServerActive() == True
            elif action == 'restart':
                return isServerActive() == True
            elif action == 'stop':
                return isServerActive() == False
        except Exception as e:
            print(f"Error : {e}")
            return False
    else:
        print(f"Please select the allowed action {', '.join(action_list)}")
        return False

def isServerActive() -> bool:
    return serverSystemd('is-active', 'zomboid')

def serverControl(action: str) -> bool:
    status = isServerActive()
    if action == 'start':
        if status == 'off':
             return serverSystemd('start', 'zomboid')
        else:
            return "Server already started!"
    elif action == 'off':
        if status == 'on':
            return serverSystemd('stop', 'zomboid')
        else:
            return "Server is not started!"
    elif action == 'restart':
        if status == 'on':
            return serverSystemd('restart', 'zomboid')
        else:
            return " Server is not started!"
    else:
        return

    
if __name__ == '__main__':
    app.run()