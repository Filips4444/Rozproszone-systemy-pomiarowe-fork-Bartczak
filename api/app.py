from flask import Flask, jsonify
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
            .container { max-width: 800px; background: white; padding: 20px; border-radius: 8px; box-shadow: 0 2px 10px rgba(0,0,0,0.1); }
            h1 { color: #333; border-bottom: 2px solid #eee; padding-bottom: 10px; }
            .nav-link { 
                display: inline-block; 
                margin-right: 15px; 
                padding: 10px 20px; 
                background-color: #007bff; 
                color: white; 
                text-decoration: none; 
                border-radius: 5px; 
            }
            .nav-link:hover { background-color: #0056b3; }
            .info-box { background: #e7f3ff; border-left: 5px solid #2196F3; padding: 10px; margin: 20px 0; }
            code { background: #eee; padding: 2px 5px; }
        </style>
    </head>
    <body>
        <div class="container">
            <h1>System Monitoringu Pomiarów</h1>
            <div class="info-box">
                <strong>Status systemu:</strong> Serwer działa poprawnie na porcie 5001.
            </div>
            
            <h3>Dostępne opcje:</h3>
            <p>Wybierz jedną z poniższych sekcji, aby zarządzać danymi:</p>
            
            <a href="/measurements" class="nav-link">Pokaż pomiary (JSON)</a>
            <a href="/health" class="nav-link" style="background-color: #28a745;">Sprawdź Healthcheck</a>

            <hr>
            <h3>Dokumentacja API:</h3>
            <ul>
                <li><code>GET /measurements</code> - Pobiera 20 najnowszych rekordów z bazy danych.</li>
                <li><code>GET /health</code> - Zwraca status 200 OK w formacie JSON.</li>
            </ul>
        </div>
    </body>
    </html>
    """

@app.route("/health", methods=["GET"])
def health():
    return jsonify({"status": "ok"})

@app.route("/measurements")
def get_measurements():
    conn = get_connection()
    cur = conn.cursor()
    cur.execute("""
        SELECT id, group_id, device_id, sensor, value, unit, ts_ms, seq, topic
        FROM measurements
        10
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

if __name__ == '__main__':
    app.run(debug=True, host='0.0.0.0', port=5001)
