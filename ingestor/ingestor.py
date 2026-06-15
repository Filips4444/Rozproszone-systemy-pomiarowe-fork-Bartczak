import json
import paho.mqtt.client as mqtt
from db import get_connection

MQTT_HOST = "broker"
MQTT_PORT = 1883
MQTT_TOPIC = "lab/+/+/+"


def is_valid(data):
    required = ["device_id", "sensor", "value", "ts_ms"]
    for field in required:
        if field not in data:
            print(f"Missing required field: {field}")
            return False

    if not isinstance(data["device_id"], str) or len(data["device_id"]) == 0:
        print("Invalid device_id: must be a non-empty string")
        return False

    if not isinstance(data["sensor"], str) or len(data["sensor"]) == 0:
        print("Invalid sensor: must be a non-empty string")
        return False

    if not isinstance(data["value"], (int, float)):
        print("Invalid value: must be a number")
        return False

    if not isinstance(data["ts_ms"], int) or data["ts_ms"] <= 0:
        print("Invalid ts_ms: must be a positive integer")
        return False

    return True


def save_measurement(topic, data):
    conn = get_connection()
    cur = conn.cursor()
    cur.execute("""
        INSERT INTO measurements
            (group_id, device_id, sensor, value, unit, ts_ms, seq, topic)
        VALUES (%s, %s, %s, %s, %s, %s, %s, %s)
    """, (
        data.get("group_id"),
        data["device_id"],
        data["sensor"],
        data["value"],
        data.get("unit"),
        data["ts_ms"],
        data.get("seq"),
        topic
    ))
    conn.commit()
    cur.close()
    conn.close()


def on_connect(client, userdata, flags, rc, properties=None):
    print(f"Connected to MQTT broker with result code {rc}")
    client.subscribe(MQTT_TOPIC)
    print(f"Subscribed to topic: {MQTT_TOPIC}")


def on_message(client, userdata, msg):
    try:
        payload = msg.payload.decode("utf-8")
        data = json.loads(payload)

        if not is_valid(data):
            print(f"Invalid payload on {msg.topic}: {payload}")
            return

        save_measurement(msg.topic, data)
        print(f"Saved measurement from {msg.topic}: device={data['device_id']}, "
              f"sensor={data['sensor']}, value={data['value']}")

    except json.JSONDecodeError:
        print(f"Invalid JSON on {msg.topic}: {msg.payload}")
    except Exception as e:
        print(f"Error processing message: {e}")


client = mqtt.Client(mqtt.CallbackAPIVersion.VERSION2)
client.on_connect = on_connect
client.on_message = on_message

print(f"Connecting to MQTT broker at {MQTT_HOST}:{MQTT_PORT}...")
client.connect(MQTT_HOST, MQTT_PORT, 60)
client.loop_forever()