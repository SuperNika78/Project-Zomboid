import subprocess
import os
import json
import psutil
import threading
import time
from flask import Flask, request, jsonify
from flask_cors import CORS

class ZomboidServerManager:
    def __init__(self, server_path='/home/gameserver/projectzomboid'):
        self.server_path = server_path
        self.server_process = None
        self.server_log_file = os.path.join(server_path, 'server.log')
        self.config_file = os.path.join(server_path, 'server.cfg')

    def start_server(self, config):
        # Cek apakah server sudah berjalan
        if self.is_server_running():
            return False, "Server sudah aktif"

        # Perbarui konfigurasi server
        self._update_server(config)

        # Perintah untuk memulai server
        start_command = [
            'java', 
            '-Xmx4096m',  # Alokasi memori
            '-jar', 
            os.path.join(self.server_path, 'zomboid-server.jar'),
            '-config', self.config_file
        ]

        try:
            # Jalankan server di background
            self.server_process = subprocess.Popen(
                start_command, 
                cwd=self.server_path,
                stdout=open(self.server_log_file, 'w'),
                stderr=subprocess.STDOUT
            )
            return True, "Server berhasil dimulai"
        except Exception as e:
            return False, f"Gagal memulai server: {str(e)}"

    def stop_server(self):
        if not self.is_server_running():
            return False, "Server tidak aktif"

        try:
            # Kirim sinyal terminate ke proses
            self.server_process.terminate()
            
            # Tunggu proses berhenti
            self.server_process.wait(timeout=10)
            
            return True, "Server berhasil dihentikan"
        except subprocess.TimeoutExpired:
            # Paksa kill jika tidak mau berhenti
            self.server_process.kill()
            return True, "Server dipaksa berhenti"
        except Exception as e:
            return False, f"Gagal menghentikan server: {str(e)}"

    def is_server_running(self):
        if not self.server_process:
            return False
        
        try:
            # Periksa status proses
            return self.server_process.poll() is None
        except:
            return False

    def get_server(self):
        if not self.is_server_running():
            return {
                'status': 'stopped',
                'players': 0,
                'uptime': 0
            }

        # Baca log untuk informasi tambahan
        try:
            with open(self.server_log_file, 'r') as log:
                log_content = log.readlines()
                players = self._count_players(log_content)
                uptime = self._calculate_uptime()
            
            return {
                'status': 'running',
                'players': players,
                'uptime': uptime
            }
        except:
            return {
                'status': 'unknown',
                'players': 0,
                'uptime': 0
            }

    def _update_server(self, config):
        # Buat file konfigurasi
        config_content = f"""
server_name={config.get('name', 'Zomboid Server')}
max_players={config.get('maxPlayers', 8)}
game_mode={config.get('pvp', False)}
map={config.get('mapName', 'Muldraugh, Kentucky')}
"""
        with open(self.config_file, 'w') as f:
            f.write(config_content)

    def _count_players(self, log_lines):
        # Logika sederhana untuk menghitung pemain dari log
        return sum(1 for line in log_lines if 'player connected' in line.lower())

    def _calculate_uptime(self):
        # Hitung waktu server berjalan
        if not self.server_process:
            return 0
        
        try:
            create_time = psutil.Process(self.server_process.pid).create_time()
            return int(time.time() - create_time)
        except:
            return 0

# Inisialisasi Flask API
app = Flask(__name__)
CORS(app)
server_manager = ZomboidServerManager()

@app.route('/server/start', methods=['POST'])
def start_server():
    config = request.json
    success, message = server_manager.start_server(config)
    return jsonify({
        'success': success, 
        'message': message
    })

@app.route('/server/stop', methods=['POST'])
def stop_server():
    success, message = server_manager.stop_server()
    return jsonify({
        'success': success, 
        'message': message
    })

@app.route('/server/status', methods=['GET'])
def get_server():
    status = server_manager.get_server()
    return jsonify(status)

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000)