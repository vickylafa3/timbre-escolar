from flask import Flask, jsonify, request
import json
import os
import requests  # 🔹 para comunicar con el ESP32

app = Flask(__name__)

CONFIG_FILE = "config_timbre.json"

def load_config():
    if not os.path.exists(CONFIG_FILE):
        return {}
    with open(CONFIG_FILE, "r", encoding="utf-8") as f:
        return json.load(f)

def save_config(data):
    with open(CONFIG_FILE, "w", encoding="utf-8") as f:
        json.dump(data, f, indent=2, ensure_ascii=False)

# 🔹 Ruta para obtener toda la configuración
@app.route("/config", methods=["GET"])
def get_config():
    return jsonify(load_config())

# 🔹 Ruta para actualizar toda la configuración
@app.route("/config", methods=["POST"])
def update_config():
    data = request.json
    if not data:
        return jsonify({"error": "No se envió ningún JSON"}), 400
    save_config(data)
    return jsonify({"message": "Configuración actualizada correctamente"})

# 🔹 Ruta para cambiar una clave específica
@app.route("/config/<key>", methods=["PATCH"])
def update_key(key):
    config = load_config()
    if key not in config:
        return jsonify({"error": f"La clave '{key}' no existe"}), 404
    value = request.json.get("value")
    config[key] = value
    save_config(config)
    return jsonify({"message": f"'{key}' actualizada", "nuevo_valor": value})

# 🔹 Ruta para obtener horarios por turno
@app.route("/horarios/<turno>", methods=["GET"])
def get_horarios(turno):
    config = load_config()
    key = f"horarios_personalizados_{turno}"
    if key not in config:
        return jsonify({"error": f"No existe el turno '{turno}'"}), 404
    return jsonify(config[key])

# 🔹 Ruta para actualizar horarios de un turno
@app.route("/horarios/<turno>", methods=["POST"])
def update_horarios(turno):
    config = load_config()
    key = f"horarios_personalizados_{turno}"
    nuevos_horarios = request.json
    if not isinstance(nuevos_horarios, list):
        return jsonify({"error": "El cuerpo debe ser una lista de horarios"}), 400
    config[key] = nuevos_horarios
    save_config(config)
    return jsonify({"message": f"Horarios del turno '{turno}' actualizados correctamente"})

# 🔹 Ruta para registrar o actualizar la IP del ESP32
@app.route("/esp32/register", methods=["POST"])
def register_esp32():
    ip = request.remote_addr  # IP real del dispositivo que hace la petición
    config = load_config()
    config["ultimo_esp32_ip"] = ip
    save_config(config)
    print(f"📡 ESP32 conectado desde {ip}")
    return jsonify({"message": "ESP32 registrado", "ip": ip})

# 🔹 Ruta para activar el timbre (desde app o PC)
@app.route("/timbrar", methods=["POST"])
def timbrar():
    tipo = request.json.get("tipo", "manual")
    config = load_config()
    esp_ip = config.get("ultimo_esp32_ip")

    if not esp_ip:
        return jsonify({"error": "No hay ESP32 registrado"}), 404

    try:
        # 🔹 Se envía la orden al ESP32
        response = requests.post(f"http://{esp_ip}/ring", json={"tipo": tipo}, timeout=5)
        if response.status_code == 200:
            return jsonify({"message": f"Timbre activado ({tipo}) vía ESP32"})
        else:
            return jsonify({"error": f"ESP32 respondió con error {response.status_code}"})
    except requests.RequestException as e:
        return jsonify({"error": f"No se pudo contactar al ESP32: {e}"})

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000, debug=True)
