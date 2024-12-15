import os
import dotenv
import time
import secrets
from pathlib import Path
from flask import *
import sys
import json
import random
from hashlib import sha256

sys.path.append(str(Path(__file__).resolve().parent))

root_dir = Path(os.getcwd())
static_dir = root_dir / 'static'

dotenv.load_dotenv(root_dir / '.env')

app = Flask(__name__)
app.secret_key = os.getenv("SUPER_SECRETE_KEY") if os.getenv(
    "SUPER_SECRETE_KEY") else secrets.token_hex(16)


users: dict[str] = json.loads(os.getenv("USERS")) if os.getenv("USERS") else {}

with open(Path(os.getcwd()) / Path(os.getenv("DEVICES_PATH").strip('"'))) as r:
    devices: dict = json.load(r)

with open(Path(os.getcwd()) / Path(os.getenv("PRESETS_PATH").strip('"'))) as r:
    presets = json.load(r)

with open(Path(os.getcwd()) / Path(os.getenv("UTILS_PATH").strip('"'))) as r:
    utils = json.load(r)


def analyzediseasehandler(username: str, device: str) -> json:
    time.sleep(1)
    return utils[random.randint(0, len(utils)-1)]


def wateringhandler(username: str, device: str) -> json:
    time.sleep(0.5)
    return True


def lightinghandler(username: str, device: str) -> json:
    time.sleep(0.5)
    return True


def historyhandler(username: str, device: str) -> list[str] | list:
    if username not in devices.keys():
        return []
    time.sleep(0.5)
    return devices[username][device]["history"]


def strhashcode(s: str) -> str:
    return sha256(s.encode('utf-8')).hexdigest()


def getdevices(username: str) -> list[str] | list:
    if username not in devices.keys():
        return []
    return devices[username]


def getdevicedefault() -> dict:
    return {
        "preset": None,
        "temperature": random.randint(20, 28),
        "moisture": random.randint(35, 85),
        "light": random.randint(300, 1200),
        "lastwateredtime": None,
        "noti": True,
        "history": []
    }


@app.route('/static/<path:path>')
def servestaticfiles(path):
    return send_from_directory('static', path)


@app.route("/", methods=["GET"])
def index():
    if "username" not in session:
        return redirect(url_for("login")), 302

    username = session["username"]
    if username == "admin@muruk":
        return render_template("admin.html"), 200
    user_devices = devices.get(username, {})

    enriched_devices = []
    for device_id, device_info in user_devices.items():
        preset_key = device_info.get("preset")
        preset = presets.get(preset_key, {})

        enriched_devices.append({
            "device_id": device_id,
            "plant_name": preset.get("plantName", "Unknown Plant"),
            "min_temp": preset.get("minTemp", "N/A"),
            "max_temp": preset.get("maxTemp", "N/A"),
            "min_moisture": preset.get("minMoisture", "N/A"),
            "max_moisture": preset.get("maxMoisture", "N/A"),
            "min_light": preset.get("minLight", "N/A"),
            "max_light": preset.get("maxLight", "N/A"),
            "optimal_water": preset.get("optimalWaterAmount", "N/A"),
            "current_temp": device_info.get("temperature", "N/A"),
            "current_moisture": device_info.get("moisture", "N/A"),
            "current_light": device_info.get("light", "N/A"),
            "last_watered": device_info.get("lastwateredtime", "N/A")
        })
    return render_template(
        "index.html",
        username=username,
        devices=enriched_devices
    ), 200


@app.route('/login', methods=['GET', 'POST'])
def login():
    if "username" in session:
        username = session["username"]
        if username == "admin@muruk":
            return render_template("admin.html"), 200
        return redirect(url_for("index"))
    if request.method == "POST":
        username = request.form.get("username")
        password = strhashcode(request.form.get("password"))

        if username == "admin@muruk" and users[username] == password:
            session["username"] = username
            return render_template(
                "admin.html",
                username=username,
            ), 200

        if username in users and users[username] == password:
            session["username"] = username
            flash("Login successful!", "success")
            return redirect(url_for("index")), 302

        flash("Invalid credentials. Please try again.", "danger")
        return render_template("login.html"), 401

    return render_template("login.html"), 200


@app.route('/listpreset', methods=['GET'])
def listpreset():
    return jsonify({'status': 200, 'message': 'Successfully loaded the presets', 'data': {'presets': presets}}), 200


@app.route('/registerpreset', methods=['POST'])
def registerpreset():
    if "username" not in session:
        return redirect(url_for("login")), 302
    username = session["username"]
    if username != "admin@muruk":
        return redirect(url_for("index")), 302

    data = request.json

    preset_id = data.get("preset_id")
    if not preset_id or preset_id in presets.keys():
        return jsonify({'status': 400, 'message': 'Invalid or duplicate preset ID'}), 400

    required_fields = ["plantName", "minTemp", "maxTemp", "minMoisture", "maxMoisture",
                       "minLight", "maxLight", "minFloweringDarkness", "optimalWaterAmount"]
    if not all(field in data for field in required_fields):
        return jsonify({'status': 400, 'message': 'Missing required fields'}), 400

    presets[preset_id] = {
        "plantName": data["plantName"],
        "minTemp": data["minTemp"],
        "maxTemp": data["maxTemp"],
        "minMoisture": data["minMoisture"],
        "maxMoisture": data["maxMoisture"],
        "minLight": data["minLight"],
        "maxLight": data["maxLight"],
        "minFloweringDarkness": data["minFloweringDarkness"],
        "optimalWaterAmount": data["optimalWaterAmount"],
    }

    return jsonify({'status': 200, 'message': 'Preset registered successfully'}), 200


@app.route('/updatepreset/<string:preset_id>', methods=['POST'])
def updatepreset(preset_id):
    if "username" not in session:
        return redirect(url_for("login")), 302

    username = session["username"]
    if username != "admin@muruk":
        return redirect(url_for("index")), 302

    if preset_id not in presets:
        return jsonify({'status': 404, 'message': 'Preset not found'}), 404

    data = request.json
    for key, value in data.items():
        if key in presets[preset_id]:
            presets[preset_id][key] = value

    return jsonify({'status': 200, 'message': 'Preset updated successfully'}), 200


@app.route("/logout")
def logout():
    session.pop("username", None)
    flash("You have been logged out.", "info")
    return redirect(url_for('index')), 302


@app.route('/signup', methods=['GET', 'POST'])
def signup():
    if "username" in session:
        return redirect(url_for("index")), 302

    if request.method == "POST":
        username = request.form.get("username")
        password = strhashcode(request.form.get("password"))

        if len(username) < 3 or len(password) < 4:
            flash(
                "Username must be at least 3 characters and password at least 4 characters.", "danger")
            return render_template("login.html"), 400

        if not username or not password:
            flash("Username and password are required.", "danger")
            return render_template("signup.html")

        if username not in users:
            users[username] = password
            flash("Sign Up successful! Please log in.", "success")
            return redirect(url_for("login")), 302
        else:
            flash("Username already exists. Please choose a different one.", "danger")

    return render_template("signup.html"), 200


@app.route('/forgotmypw', methods=['GET'])
def forgotmypw():
    if "username" in session:
        return redirect(url_for("index")), 302

    return render_template("forgotmypw.html"), 200


@app.route('/registerdevice', methods=['GET', 'POST'])
def registerdevice():
    if "username" not in session:
        return redirect(url_for("login")), 302

    if request.method == "POST":
        devicecode = request.form.get("devicecode")
        if not devicecode:
            return jsonify({'message': 'Device Code is required.'}), 400

        username = session["username"]

        if username not in devices.keys() or devicecode not in devices[username]:
            devices[username][devicecode] = getdevicedefault()
            flash('Successfully registered', 'message')
            return render_template("registerdevicesuccess.html"), 200
        else:
            flash('Already registered device', 'message')
            return redirect(url_for("registerdevice")), 302
    return render_template("registerdevice.html"), 200


@app.route('/registerdevicebyqr/<string:devicecode>', methods=['GET'])
def registerdevicebyqr(devicecode: str):
    if "username" not in session:
        return redirect(url_for("login")), 302

    if not devicecode:
        return jsonify({'message': 'Device Code is required.'}), 400

    username = session["username"]

    if username not in devices.keys() or devicecode not in devices[username]:
        devices[username][devicecode] = getdevicedefault()
        flash('Successfully registered', 'message')
        return render_template("registerdevicesuccess.html"), 200
    flash('Already registered device', 'message')
    return redirect(url_for("registerdevice")), 302


@app.route('/setpreset/<string:device>', methods=['GET'])
def setpreset(device: str, ):
    if "username" not in session:
        return redirect(url_for("login")), 302

    username = session["username"]
    if username not in devices.keys() or device not in devices[username]:
        return jsonify({'status': 200, 'message': 'No devices detected', 'data': {'result': []}}), 200

    preset = request.args.get('preset')
    if preset not in ["preset001", "preset002", "preset003", "preset004", "preset005"]:
        return jsonify({'status': 200, 'message': 'No presets detected', 'data': {'result': []}}), 200

    devices[username][device]["preset"] = preset
    return jsonify({'status': 200, 'message': 'Successfully set your preset', 'data': {'result': True}}), 200


@app.route('/setnoti/<string:device>', methods=['GET'])
def setnoti(device: str, ):
    if "username" not in session:
        return redirect(url_for("login")), 302

    username = session["username"]
    if username not in devices.keys() or device not in devices[username]:
        return jsonify({'status': 200, 'message': 'No devices detected', 'data': {'result': None}}), 200

    noti_data = request.args.get('noti')
    if noti_data.lower() not in ["true", "false"]:
        return jsonify({'status': 200, 'message': 'No presets detected', 'data': {'result': None}}), 200

    devices[username][device]["noti"] = noti_data.lower()
    return jsonify({'status': 200, 'message': 'Successfully set your preset', 'data': {'result': noti_data.lower()}}), 200


@app.route('/noti/<string:device>', methods=['GET'])
def noti(device: str, ):
    if "username" not in session:
        return redirect(url_for("login")), 302

    username = session["username"]
    if username not in devices.keys() or device not in devices[username]:
        return jsonify({'status': 200, 'message': 'No devices detected', 'data': {'result': None}}), 200

    return jsonify({'status': 200, 'message': 'Successfully set your preset', 'data': {'result': devices[username][device]["noti"]}}), 200


@app.route('/listdevice', methods=['GET'])
def listdevice():
    if "username" not in session:
        return redirect(url_for("login")), 302
    username = session["username"]
    if username not in devices.keys():
        return jsonify({'status': 200, 'message': 'No devices detected', 'data': {'devices': []}}), 200
    return jsonify({'status': 200, 'message': 'Successfully loaded your devices', 'data': {'devices': getdevices(username)}}), 200


@app.route('/analyzedisease/<string:device>', methods=['GET'])
def analyzedisease(device: str):
    if "username" not in session:
        return redirect(url_for("login")), 302
    username = session["username"]
    if username not in devices.keys() or device not in devices[username]:
        return jsonify({'status': 200, 'message': 'No devices detected', 'data': {'result': []}}), 200
    result = analyzediseasehandler(username, device)
    result["plantName"] = presets[devices[username]
                                  [device]["preset"]]["plantName"]
    return jsonify({'status': 200, 'message': 'Successfully loaded your devices', 'data': {'result': result}}), 200


@app.route('/water/<string:device>', methods=['GET'])
def water(device: str):
    if "username" not in session:
        return redirect(url_for("login")), 302
    username = session["username"]
    if username not in devices.keys() or device not in devices[username]:
        return jsonify({'status': 200, 'message': 'No devices detected', 'data': {'result': False}}), 200
    result = wateringhandler(username, device)
    return jsonify({'status': 200, 'message': 'Successfully watered your plant', 'data': {'result': result}}), 200


@app.route('/lightschedule/<string:device>', methods=['GET'])
def light(device: str):
    if "username" not in session:
        return redirect(url_for("login")), 302
    username = session["username"]
    if username not in devices.keys() or device not in devices[username]:
        return jsonify({'status': 200, 'message': 'No devices detected', 'data': {'result': False}}), 200
    time_sehdcule_start = request.args.get('start')
    time_sehdcule_end = request.args.get('end')
    devices[username][device]["scheduledlighting"] = f"{time_sehdcule_start} ~ {time_sehdcule_end}"
    return jsonify({'status': 200, 'message': 'Successfully lighted your plant', 'data': {'result': True}}), 200


@app.route('/scheduledlight/<string:device>', methods=['GET'])
def scheduledlight(device: str):
    if "username" not in session:
        return redirect(url_for("login")), 302
    username = session["username"]
    if username not in devices.keys() or device not in devices[username]:
        return jsonify({'status': 200, 'message': 'No devices detected', 'data': {'result': None}}), 200
    result = devices[username][device].get("scheduledlighting", "")
    if result == "":
        return jsonify({'status': 200, 'message': 'No devices detected', 'data': {'result': None}}), 200
    return jsonify({'status': 200, 'message': 'Successfully loaded your lighting schedule', 'data': {'result': result}}), 200


@app.route('/history/<string:device>', methods=['GET'])
def history(device: str):
    if "username" not in session:
        return redirect(url_for("login")), 302
    username = session["username"]
    if username not in devices.keys() or device not in devices[username]:
        return jsonify({'status': 200, 'message': 'No devices detected', 'data': {'result': []}}), 200
    result = historyhandler(username, device)
    return jsonify({'status': 200, 'message': 'Successfully loaded your history', 'data': {'result': result}}), 200


if __name__ == '__main__':
    app.run(debug=True, port=8000)
