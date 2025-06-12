import xml.etree.ElementTree as ET
import pandas as pd
import matplotlib.pyplot as plt
import os
import time  # time modülü eklendi
import json
import paho.mqtt.client as mqtt
import sys

# === MQTT AYARI ===
def on_connect(c, u, f, rc):
    print("[MQTT] Bağlandı. Kod:", rc)
    c.subscribe("evse/response")
def on_message(c, u, msg):
    print(f"[MQTT] Gelen mesaj: {msg.topic} - {msg.payload.decode()}")

client = mqtt.Client()
client.on_connect = on_connect
client.on_message = on_message
client.connect("broker.hivemq.com", 1883, 60)
client.loop_start()

# === XML DOSYASI ===
file_path = "trips.xml"  # XML dosyasının yolu
if not os.path.exists(file_path):
    print(f"{file_path} bulunamadı.")
    sys.exit(1)

tree = ET.parse(file_path)
root = tree.getroot()

# === VERİ TOPLAMA ===
rows = []
for trip in root.findall("trip"):
    vid = trip.get("id")
    dep = float(trip.get("depart", 0.0))
    dur = trip.get("duration")
    dur = float(dur) if dur is not None else 0.0
    arr = dep + dur
    rows.append((vid, dep, dur, arr))

df = pd.DataFrame(rows, columns=["vehicle_id","depart_time","trip_duration","arrival_time"])

# === PARK SÜRESİ & ENERJİ ===
df["park_start"]   = df["arrival_time"] - 60       # 1 dak. park
df["park_duration"]= df["park_start"] - df["depart_time"]
df["energy_kWh"]   = df["trip_duration"] * 0.2

# === ZAMAN DÖNÜŞÜM & GRUPLAMA ===
df["depart_dt"] = pd.to_datetime(df["depart_time"], unit="s", origin="unix")
bins = pd.date_range("00:00:00","23:59:59",freq="H")
df["time_bin"] = pd.cut(df["depart_dt"], bins=bins)
summary = df.groupby("time_bin")["park_duration"].sum().reset_index()

# === GRAFİK ===
fig, ax = plt.subplots(figsize=(12,6))
ax.plot(summary["time_bin"].astype(str), summary["park_duration"], marker="o")
ax.set_xticklabels(summary["time_bin"].astype(str), rotation=45)
ax.set_xlabel("Saat Dilimi")
ax.set_ylabel("Toplam Park Süresi (saniye)")
ax.set_title("V2G Enerji Çekişi İçin Park Süreleri")
ax.grid(True)
plt.tight_layout()
plt.show()

# === V2G_FEEDBACK MESAJI ===
for _, r in df.iterrows():
    if r["park_duration"] > 30:
        msg = {"vehicle_id": r["vehicle_id"], "action": "v2g_feedback", "amount_kWh": r["energy_kWh"]}
        client.publish("evse/cmd", json.dumps(msg))
        time.sleep(0.5)  # Bekleme süresi eklendi
