from flask import Flask, jsonify, request
import json
import os

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
    config = load_config()
    return jsonify(config)

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
        return jsonify({"error": f"La clave '{key}' no existe en la configuración"}), 404

    value = request.json.get("value")
    config[key] = value
    save_config(config)
    return jsonify({"message": f"'{key}' actualizada", "nuevo_valor": value})

# 🔹 Ruta para obtener horarios por turno (mañana o tarde)
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
    if key not in config:
        return jsonify({"error": f"No existe el turno '{turno}'"}), 404

    nuevos_horarios = request.json
    if not isinstance(nuevos_horarios, list):
        return jsonify({"error": "El cuerpo debe ser una lista de horarios"}), 400

    config[key] = nuevos_horarios
    save_config(config)
    return jsonify({"message": f"Horarios del turno '{turno}' actualizados correctamente"})

# 🔹 Ruta opcional: cambiar IP del ESP32
@app.route("/esp32/ip", methods=["PATCH"])
def update_esp32_ip():
    config = load_config()
    nueva_ip = request.json.get("ip")
    if not nueva_ip:
        return jsonify({"error": "Falta el campo 'ip'"}), 400

    config["ultimo_esp32_ip"] = nueva_ip
    save_config(config)
    return jsonify({"message": "IP del ESP32 actualizada", "ip": nueva_ip})

# 🔹 Ruta opcional: timbrar manualmente (simulado)
@app.route("/timbrar", methods=["POST"])
def timbrar():
    tipo = request.json.get("tipo", "manual")
    print(f"🛎️ Timbre activado ({tipo})")
    # Aquí podrías hacer un request al ESP32 real
    return jsonify({"message": f"Timbre activado ({tipo})"})

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000, debug=True)