from flask import Flask, jsonify, request
from datetime import datetime
import json
import os

app = Flask(__name__)
CONFIG_FILE = "config_timbre.json"

def load_config():
    if not os.path.exists(CONFIG_FILE):
        # Configuración inicial con campo de orden
        return {
            "orden": "ninguna",
            "duracion_timbre": 5,
            "horarios_habilitados": False,
            "ultima_modificacion": None
        }
    with open(CONFIG_FILE, "r", encoding="utf-8") as f:
        return json.load(f)

def save_config(data):
    with open(CONFIG_FILE, "w", encoding="utf-8") as f:
        json.dump(data, f, indent=2, ensure_ascii=False)

# ============================================
# 🔹 RUTA PRINCIPAL - GET/POST /config
# ============================================
@app.route("/config", methods=["GET", "POST"])
def config():
    if request.method == "GET":
        # ESP32 o Python consultan la configuración
        config = load_config()
        return jsonify(config)
    
    elif request.method == "POST":
        data = request.json
        if not data:
            return jsonify({"error": "No se envió ningún JSON"}), 400
        
        config = load_config()
        
        # ⭐ CASO 1: Orden de timbre desde Python
        if "orden" in data and data["orden"] == "timbrar":
            config["orden"] = "timbrar"
            config["duracion_timbre"] = data.get("duracion_timbre", 5)
            config["timestamp_orden"] = datetime.now().isoformat()
            save_config(config)
            
            print("="*60)
            print("🔔 ORDEN DE TIMBRE RECIBIDA DESDE PYTHON")
            print("="*60)
            print(f"  ⏰ Duración: {config['duracion_timbre']} segundos")
            print(f"  📅 Timestamp: {config['timestamp_orden']}")
            print(f"  📡 ESP32 recogerá esta orden en máximo 5 segundos")
            print("="*60 + "\n")
            
            return jsonify({
                "status": "ok",
                "mensaje": "Orden de timbre registrada",
                "duracion": config["duracion_timbre"]
            })
        
        # ⭐ CASO 2: ESP32 limpia la orden después de ejecutarla
        elif "orden" in data and data["orden"] == "ninguna":
            config["orden"] = "ninguna"
            config["timestamp_ejecutado"] = datetime.now().isoformat()
            save_config(config)
            
            print("="*60)
            print("✅ ORDEN EJECUTADA POR ESP32")
            print("="*60)
            print(f"  📅 Timestamp: {config['timestamp_ejecutado']}")
            print(f"  🔕 Orden limpiada del servidor")
            print("="*60 + "\n")
            
            return jsonify({
                "status": "ok",
                "mensaje": "Orden ejecutada"
            })
        
        # ⭐ CASO 3: Actualización normal de configuración
        else:
            config.update(data)
            config["ultima_modificacion"] = datetime.now().isoformat()
            save_config(config)
            
            print(f"📝 Configuración actualizada: {list(data.keys())}")
            
            return jsonify({
                "status": "ok",
                "mensaje": "Configuración actualizada correctamente"
            })

# ============================================
# 🔹 Ruta para cambiar una clave específica
# ============================================
@app.route("/config/<key>", methods=["PATCH"])
def update_key(key):
    config = load_config()
    if key not in config:
        return jsonify({"error": f"La clave '{key}' no existe en la configuración"}), 404
    
    value = request.json.get("value")
    config[key] = value
    config["ultima_modificacion"] = datetime.now().isoformat()
    save_config(config)
    
    return jsonify({"message": f"'{key}' actualizada", "nuevo_valor": value})

# ============================================
# 🔹 Ruta para obtener horarios por turno
# ============================================
@app.route("/horarios/<turno>", methods=["GET"])
def get_horarios(turno):
    config = load_config()
    key = f"horarios_personalizados_{turno}"
    if key not in config:
        return jsonify({"error": f"No existe el turno '{turno}'"}), 404
    return jsonify(config[key])

# ============================================
# 🔹 Ruta para actualizar horarios de un turno
# ============================================
@app.route("/horarios/<turno>", methods=["POST"])
def update_horarios(turno):
    config = load_config()
    key = f"horarios_personalizados_{turno}"
    
    nuevos_horarios = request.json
    if not isinstance(nuevos_horarios, list):
        return jsonify({"error": "El cuerpo debe ser una lista de horarios"}), 400
    
    config[key] = nuevos_horarios
    config["ultima_modificacion"] = datetime.now().isoformat()
    save_config(config)
    
    print(f"📅 Horarios del turno '{turno}' actualizados: {len(nuevos_horarios)} horarios")
    
    return jsonify({"message": f"Horarios del turno '{turno}' actualizados correctamente"})

# ============================================
# 🔹 Ruta para actualizar IP del ESP32
# ============================================
@app.route("/esp32/ip", methods=["PATCH"])
def update_esp32_ip():
    config = load_config()
    nueva_ip = request.json.get("ip")
    if not nueva_ip:
        return jsonify({"error": "Falta el campo 'ip'"}), 400
    
    config["ultimo_esp32_ip"] = nueva_ip
    config["ultima_modificacion"] = datetime.now().isoformat()
    save_config(config)
    
    return jsonify({"message": "IP del ESP32 actualizada", "ip": nueva_ip})

# ============================================
# 🔹 NUEVA RUTA: Estado del sistema
# ============================================
@app.route("/status", methods=["GET"])
def status():
    config = load_config()
    
    return jsonify({
        "servidor": "online",
        "timestamp": datetime.now().isoformat(),
        "orden_pendiente": config.get("orden", "ninguna"),
        "duracion_timbre": config.get("duracion_timbre", 5),
        "horarios_activos": config.get("horarios_habilitados", False),
        "ultima_modificacion": config.get("ultima_modificacion", None)
    })

# ============================================
# 🔹 NUEVA RUTA: Limpiar orden manualmente
# ============================================
@app.route("/limpiar_orden", methods=["POST"])
def limpiar_orden():
    config = load_config()
    config["orden"] = "ninguna"
    save_config(config)
    
    print("🧹 Orden limpiada manualmente desde endpoint")
    
    return jsonify({
        "status": "ok",
        "mensaje": "Orden limpiada"
    })

# ============================================
# 🔹 Ruta raíz - Panel de información
# ============================================
@app.route("/", methods=["GET"])
def home():
    config = load_config()
    
    html = f"""
    <!DOCTYPE html>
    <html>
    <head>
        <title>🔔 Sistema de Timbre Escolar</title>
        <meta charset="utf-8">
        <style>
            body {{
                font-family: 'Segoe UI', Arial, sans-serif;
                max-width: 800px;
                margin: 50px auto;
                padding: 20px;
                background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
                color: white;
            }}
            .container {{
                background: rgba(255, 255, 255, 0.95);
                padding: 30px;
                border-radius: 15px;
                box-shadow: 0 8px 32px rgba(0,0,0,0.3);
                color: #333;
            }}
            h1 {{
                text-align: center;
                color: #667eea;
                margin-bottom: 30px;
            }}
            .status {{
                background: #f0f4ff;
                padding: 20px;
                border-radius: 10px;
                margin: 15px 0;
                border-left: 4px solid #667eea;
            }}
            .status-item {{
                margin: 10px 0;
                font-size: 16px;
            }}
            .badge {{
                display: inline-block;
                padding: 5px 15px;
                border-radius: 20px;
                font-weight: bold;
                font-size: 14px;
            }}
            .badge-success {{
                background: #10b981;
                color: white;
            }}
            .badge-warning {{
                background: #f59e0b;
                color: white;
            }}
            .badge-danger {{
                background: #ef4444;
                color: white;
            }}
            .endpoints {{
                background: #1e293b;
                color: #e2e8f0;
                padding: 20px;
                border-radius: 10px;
                margin: 20px 0;
                font-family: 'Courier New', monospace;
            }}
            .endpoint {{
                margin: 10px 0;
                padding: 8px;
                background: #334155;
                border-radius: 5px;
            }}
            .method {{
                color: #10b981;
                font-weight: bold;
            }}
        </style>
    </head>
    <body>
        <div class="container">
            <h1>🔔 Sistema de Timbre Escolar</h1>
            
            <div class="status">
                <h2>📊 Estado Actual</h2>
                <div class="status-item">
                    <strong>Servidor:</strong> 
                    <span class="badge badge-success">🟢 ONLINE</span>
                </div>
                <div class="status-item">
                    <strong>Orden Pendiente:</strong> 
                    <span class="badge {'badge-warning' if config.get('orden') == 'timbrar' else 'badge-success'}">
                        {config.get('orden', 'ninguna').upper()}
                    </span>
                </div>
                <div class="status-item">
                    <strong>Duración Timbre:</strong> {config.get('duracion_timbre', 5)} segundos
                </div>
                <div class="status-item">
                    <strong>Horarios Automáticos:</strong> 
                    {'✅ Activados' if config.get('horarios_habilitados') else '❌ Desactivados'}
                </div>
                <div class="status-item">
                    <strong>Última Modificación:</strong> {config.get('ultima_modificacion', 'N/A')}
                </div>
            </div>
            
            <div class="endpoints">
                <h3>📡 Endpoints Disponibles</h3>
                <div class="endpoint">
                    <span class="method">GET</span> /config - Obtener configuración completa
                </div>
                <div class="endpoint">
                    <span class="method">POST</span> /config - Actualizar configuración
                </div>
                <div class="endpoint">
                    <span class="method">GET</span> /status - Ver estado del sistema
                </div>
                <div class="endpoint">
                    <span class="method">GET</span> /horarios/mañana - Horarios turno mañana
                </div>
                <div class="endpoint">
                    <span class="method">GET</span> /horarios/tarde - Horarios turno tarde
                </div>
                <div class="endpoint">
                    <span class="method">POST</span> /limpiar_orden - Limpiar orden pendiente
                </div>
            </div>
            
            <div style="text-align: center; margin-top: 30px; color: #64748b;">
                <p>🕐 Timestamp: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}</p>
            </div>
        </div>
    </body>
    </html>
    """
    
    return html

# ============================================
# 🔹 Iniciar servidor
# ============================================
if __name__ == "__main__":
    print("\n" + "="*60)
    print("🚀 INICIANDO SERVIDOR FLASK")
    print("="*60)
    print("  📡 Puerto: 5000")
    print("  🌐 Host: 0.0.0.0 (accesible desde la red)")
    print("  📁 Archivo config: config_timbre.json")
    print("="*60 + "\n")
    
    # Crear archivo de configuración si no existe
    if not os.path.exists(CONFIG_FILE):
        print("📝 Creando archivo de configuración inicial...")
        save_config({
            "orden": "ninguna",
            "duracion_timbre": 5,
            "horarios_habilitados": False,
            "ultima_modificacion": datetime.now().isoformat()
        })
        print("✅ Archivo creado\n")
    
    app.run(host="0.0.0.0", port=5000, debug=True)
