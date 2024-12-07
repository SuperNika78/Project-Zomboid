from flask import Flask, render_template, request, redirect
import sqlite3
from dotenv import load_dotenv
import os
import subprocess

app = Flask(__name__)

# Define Database Connection
_DATABASE = "/home/pzuser/Zomboid/Saves/Multiplayer/servertest/players.db"

def get_db_connection():
    conn = sqlite3.connect(_DATABASE)
    conn.row_factory = sqlite3.Row
    return conn

# Routing
@app.route('/')
def index():
    return render_template('index.html', title='Project Zomboid')

@app.route('/server')
def admin():
    total_player = getPlayerList()[0]
    server_ip = request.host.split(':')[0]
    is_active = checkServerStatus()
    server_info = {
        "ip": server_ip,
        "port": 16261,
        "is_running": is_active,
        "player_count": total_player,
        "uptime":1
    }
    return render_template('server.html', server = server_info)

@app.post('/server/<action>')
def start(action):
    serverSystemd(action, 'zomboid')
    return redirect('/server')


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
                return result.stdout.strip() == "active"
            elif action == 'stop':
                return result.stdout.strip() == "inactive"
        except Exception as e:
            print(f"Error : {e}")
            return False
    else:
        print(f"Please select the allowed action {', '.join(action_list)}")
        return False

def checkServerStatus() -> bool:
    return serverSystemd('is-active', 'zomboid')

def serverControl(action: str) -> bool:
    status = checkServerStatus()
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