from flask import Flask, jsonify, request, render_template
from db import get_connection

app = Flask(__name__)

@app.route("/", methods=["GET"])
def hello_world():
    return """
    <!DOCTYPE html>
    <html lang="pl">
    <head>
        <meta charset="UTF-8">
        <title>Panel Sterowania API</title>
        <style>
            body { font-family: sans-serif; line-height: 1.6; margin: 40px; background-color: #f4f4f9; }
            .container { max-width: 800px; margin: auto; background: white; padding: 30px; border-radius: 8px; box-shadow: 0 4px 15px rgba(0,0,0,0.1); }
            h1 { color: #333; border-bottom: 2px solid #eee; padding-bottom: 10px; margin-top: 0; }
            .button-group { display: flex; flex-wrap: wrap; gap: 15px; margin-bottom: 20px; margin-top: 15px; }
            
            .nav-link { 
                flex: 1 1 calc(50% - 15px);
                box-sizing: border-box;
                text-align: center;
                padding: 12px 20px; 
                background-color: #007bff; 
                color: white; 
                text-decoration: none; 
                border-radius: 5px;
                font-weight: bold;
                transition: background-color 0.3s, transform 0.1s;
            }
            .nav-link:hover { background-color: #0056b3; transform: translateY(-2px); }
            
            
            .nav-link.gui-btn { background-color: #17a2b8; }
            .nav-link.gui-btn:hover { background-color: #117a8b; }
            .nav-link.health-btn { background-color: #28a745; }
            .nav-link.health-btn:hover { background-color: #1e7e34; }
            
            .info-box { background: #e7f3ff; border-left: 5px solid #2196F3; padding: 15px; margin: 20px 0; border-radius: 4px; }
            code { background: #eee; padding: 3px 6px; border-radius: 4px; font-family: monospace; }
            ul { line-height: 1.8; }
        </style>
    </head>
    <body>
        <div class="container">
            <h1>System Monitoringu Pomiarów</h1>
            <div class="info-box">
                <strong>Status systemu:</strong> Serwer działa poprawnie na porcie 5001.
            </div>
            
            <h3>Dostępne interfejsy i endpointy:</h3>
            <p>Wybierz jedną z poniższych opcji, aby przejść do danych:</p>
            
            <div class="button-group">
                <a href="/dashboard" class="nav-link gui-btn">Wizualizacja Danych (GUI)</a>
                <a href="/measurements" class="nav-link">Ostatnie 20 pomiarów (JSON)</a>
                <a href="/measurements/latest" class="nav-link">Najnowszy pomiar (JSON)</a>
                <a href="/measurements/history" class="nav-link">Historia z filtrowaniem (JSON)</a>
                <a href="/health" class="nav-link health-btn">Sprawdź Healthcheck</a>
            </div>

            <hr>
            <h3>Dokumentacja API:</h3>
            <ul>
                <li><code>GET /dashboard</code> - Zwraca interfejs graficzny (wykresy HTML/JS).</li>
                <li><code>GET /measurements</code> - Pobiera 20 najnowszych rekordów z bazy danych.</li>
                <li><code>GET /measurements/latest</code> - Zwraca pojedynczy, najnowszy rekord.</li>
                <li><code>GET /measurements/history</code> - Zwraca historię pomiarów. Obsługuje parametry URL np.: <code>?device_id=esp32&sensor=temp&limit=10</code></li>
                <li><code>GET /health</code> - Zwraca status działania aplikacji w formacie JSON.</li>
            </ul>
        </div>
    </body>
    </html>
    """
@app.route("/health", methods=["GET"])
def health():
    return jsonify({"status": 1})

@app.route("/measurements")
def get_measurements():
    conn = get_connection()
    cur = conn.cursor()
    cur.execute("""
        SELECT id, group_id, device_id, sensor, value, unit, ts_ms, seq, topic
        FROM measurements
        ORDER BY id DESC
        LIMIT 20
    """)
    rows = cur.fetchall()
    cur.close()
    conn.close()

    result = []
    for row in rows:
        result.append({
            "id": row[0],
            "group_id": row[1],
            "device_id": row[2],
            "sensor": row[3],
            "value": row[4],
            "unit": row[5],
            "ts_ms": row[6],
            "seq": row[7],
            "topic": row[8]
        })
    return jsonify(result)

@app.route("/measurements/latest")
def get_latest_measurement():
    conn = get_connection()
    cur = conn.cursor()
    cur.execute("""
        SELECT id, group_id, device_id, sensor, value, unit, ts_ms, seq, topic
        FROM measurements
        ORDER BY id DESC
        LIMIT 1
    """)
    row = cur.fetchone()
    cur.close()
    conn.close()

    if row is None:
        return jsonify({"message": "Brak danych"}), 404
    
    return jsonify({
        "id": row[0],
        "group_id": row[1],
        "device_id": row[2],
        "sensor": row[3],
        "value": row[4],
        "unit": row[5],
        "ts_ms": row[6],
        "seq": row[7],
        "topic": row[8]
    })


@app.route("/measurements/history")
def get_measurement_history():
    device_id = request.args.get("device_id")
    sensor = request.args.get("sensor")
    limit = request.args.get("limit", default=20, type=int)

    conn = get_connection()
    cur = conn.cursor()

    query = """
        SELECT id, group_id, device_id, sensor, value, unit, ts_ms, seq, topic
        FROM measurements
        WHERE 1=1
    """
    params = []

    if device_id:
        query += " AND device_id = %s"
        params.append(device_id)
    if sensor:
        query += " AND sensor = %s"
        params.append(sensor)

    query += " ORDER BY id DESC LIMIT %s"
    params.append(limit)

    cur.execute(query, params)
    rows = cur.fetchall()
    
    cur.close()
    conn.close()

    result = []
    for row in rows:
        result.append({
            "id": row[0],
            "group_id": row[1],
            "device_id": row[2],
            "sensor": row[3],
            "value": row[4],
            "unit": row[5],
            "ts_ms": row[6],
            "seq": row[7],
            "topic": row[8]
        })
    return jsonify(result)


@app.route("/dashboard", methods=["GET"])
def dashboard():
    return render_template("index.html")

if __name__ == '__main__':
    app.run(debug=True, host='0.0.0.0', port=5001)
