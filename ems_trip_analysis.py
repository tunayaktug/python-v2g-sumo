import time
import numpy as np
import pandas as pd
import matplotlib.pyplot as plt
from scipy.optimize import linprog
import paho.mqtt.client as mqtt
import json

# === MQTT SETUP ===
def on_connect(c,u,f,rc):
    print("[MQTT] Bağlandı. Kod:", rc)
    c.subscribe("evse/response")
def on_message(c,u,msg):
    print(f"[MQTT] Gelen mesaj: {msg.topic} - {msg.payload.decode()}")

client = mqtt.Client()
client.on_connect = on_connect
client.on_message = on_message
client.connect("broker.hivemq.com", 1883, 60)
client.loop_start()

# === VERİ ÜRETİMİ ===
time_bins = pd.date_range("00:00:00","23:00:00",freq="H")
num_bins = len(time_bins)
vehicle_capacity = 40  # kWh
num_vehicles = 10
available_min = np.random.rand(num_bins)*60
available_cap = (available_min/60)*vehicle_capacity

# === OPTIMIZASYON ===
c = np.zeros(num_bins)
A = np.eye(num_bins)
b = available_cap
bounds = [(0,vehicle_capacity)]*num_bins
res = linprog(c, A_ub=A, b_ub=b, bounds=bounds, method="highs")

# === GRAFİK & V2G ===
if res.success:
    opt_en = res.x
    plt.figure(figsize=(12,6))
    plt.plot(time_bins, opt_en, marker="o")
    plt.xlabel("Saat Dilimi")
    plt.ylabel("Opt. Enerji (kWh)")
    plt.title("Optimizasyonlu Şarj/Boşaltma")
    plt.grid(True)
    plt.xticks(rotation=45)
    plt.tight_layout()
    plt.show()

    for tb, en in zip(time_bins, opt_en):
        if en>0:
            vid = f"veh{int(np.random.rand()*num_vehicles)}"
            msg = {"vehicle_id":vid, "action":"v2g_feedback", "amount_kWh":round(en,2)}
            client.publish("evse/cmd", json.dumps(msg))
            time.sleep(0.5)
else:
    print("Optimizasyon başarısız oldu!")
