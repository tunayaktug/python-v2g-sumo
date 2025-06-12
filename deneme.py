import traci
import paho.mqtt.client as mqtt
import json
import time
import matplotlib.pyplot as plt
import xml.etree.ElementTree as ET
import random
from ems_decision import EMSDecision

# === LOG Fonksiyonu ===
def log(message, level="INFO"):
    print(f"[{level}] {message}")

# === MQTT Ayarları ===
def on_connect(client, userdata, flags, rc):
    log(f"MQTT bağlantısı başarılı: {rc}", "MQTT")
    client.subscribe("evse/response")

def on_message(client, userdata, msg):
    log(f"MQTT mesajı alındı: {msg.topic} {msg.payload.decode()}", "MQTT")

mqtt_client = mqtt.Client()
mqtt_client.on_connect = on_connect
mqtt_client.on_message = on_message
mqtt_client.connect("broker.hivemq.com", 1883, 60)
mqtt_client.loop_start()

# === SUMO Başlat ===
sumoBinary = "sumo-gui"
sumoCmd = [sumoBinary, "-c", "osm.sumocfg"]
traci.start(sumoCmd)
log("Simülasyon başladı...")

# === EMS Başlat ===
ems = EMSDecision()

# === XML Kayıtları ===
root = ET.Element("SimulationResults")

# === Parametreler ve Başlangıç Değerleri ===
battery_capacity_kwh = 50
energy_consumption_per_m = 0.0002
CO2_AVOIDED_PER_KWH = 0.3403  # kg CO₂ / kWh

total_v2g_energy = 0.0
total_profit = 0

vehicle_id = None
vehicle_soc_kwh = (60 / 100) * battery_capacity_kwh
last_position = (0, 0)

charging_lane = "-368620842#8_0"
at_charging_station = False
charging_completed = False
charging_start_time = None

soc_history = {"times": [], "soc_percentages": []}
step_counter = 0
initial_hour = random.randint(0, 23)

try:
    MAX_SIM_STEPS = 500
    while step_counter < MAX_SIM_STEPS:
        traci.simulationStep()
        step_counter += 1

        sim_hour = (initial_hour + step_counter // 5) % 24
        sim_time = traci.simulation.getTime()

        log(f"Adım: {step_counter}, Simülasyon zamanı: {sim_time:.2f}s, Saat: {sim_hour}:00", "STEP")

        if vehicle_id is None:
            ids = traci.vehicle.getIDList()
            if ids:
                vehicle_id = ids[0]
                last_position = traci.vehicle.getPosition(vehicle_id)
                log(f"Araç tespit edildi: {vehicle_id}", "ARAÇ")

        if vehicle_id:
            if vehicle_id in traci.vehicle.getIDList():
                pos_x, pos_y = traci.vehicle.getPosition(vehicle_id)
                print(f"Araç {vehicle_id} konumu: ({pos_x}, {pos_y})")
            else:
                print(f"HATA: Araç '{vehicle_id}' şu an simülasyonda yok.")
            distance_moved = ((pos_x - last_position[0])**2 + (pos_y - last_position[1])**2)**0.5
            energy_used = distance_moved * energy_consumption_per_m * 20
            vehicle_soc_kwh -= energy_used
            vehicle_soc_kwh = max(0, vehicle_soc_kwh)
            last_position = (pos_x, pos_y)

            log(f"{vehicle_id} hareket etti → Mesafe: {distance_moved:.2f} m, Enerji tüketimi: {energy_used:.4f} kWh, SoC: {vehicle_soc_kwh:.2f} kWh", "HAREKET")
            if vehicle_id in traci.vehicle.getIDList():
                lane_id = traci.vehicle.getLaneID(vehicle_id)
            else:
                break
            if lane_id == charging_lane and not at_charging_station and not charging_completed:
                soc_percent = (vehicle_soc_kwh / battery_capacity_kwh) * 100
                log(f"{vehicle_id} şarj istasyonuna geldi. SoC: %{soc_percent:.2f}", "GELİŞ")
                arrival_elem = ET.SubElement(root, "Arrival")
                arrival_elem.set("vehicle_id", vehicle_id)
                arrival_elem.set("soc_percent", f"{soc_percent:.2f}")
                arrival_elem.set("time", f"{sim_time}")

                traci.vehicle.setSpeed(vehicle_id, 0)
                at_charging_station = True
                charging_start_time = sim_time

            if at_charging_station and not charging_completed:
                time_in_charging = sim_time - charging_start_time
                soc_percent = (vehicle_soc_kwh / battery_capacity_kwh) * 100

                price, demand, command, new_state = ems.decide(soc_percent, 1, sim_hour)
                log(f"{vehicle_id} EMS Kararı → Fiyat: {price}, Talep: {demand}, Komut: {command}, Durum: {new_state}", "EMS")

                ems_elem = ET.SubElement(root, "EMSDecision")
                ems_elem.set("vehicle_id", vehicle_id)
                ems_elem.set("price", str(price))
                ems_elem.set("demand", demand)
                ems_elem.set("command", command)
                ems_elem.set("new_state", new_state)
                ems_elem.set("time", f"{sim_time}")

                if command == "charge_command":
                    charge_amount = min(0.5, battery_capacity_kwh - vehicle_soc_kwh)
                    vehicle_soc_kwh += charge_amount
                    vehicle_soc_kwh = min(battery_capacity_kwh, vehicle_soc_kwh)
                    updated_soc = (vehicle_soc_kwh / battery_capacity_kwh) * 100

                    log(f"{vehicle_id} Şarj oluyor → +{charge_amount:.2f} kWh → SoC: %{updated_soc:.2f}", "ŞARJ")

                    charge_elem = ET.SubElement(root, "Charge")
                    charge_elem.set("vehicle_id", vehicle_id)
                    charge_elem.set("amount_kWh", f"{charge_amount:.2f}")
                    charge_elem.set("new_soc_percent", f"{updated_soc:.2f}")
                    charge_elem.set("time", f"{sim_time}")

                    mqtt_client.publish("evse/cmd", json.dumps({
                        "vehicle_id": vehicle_id,
                        "action": "v2g_charge",
                        "amount_kWh": charge_amount
                    }))

                    total_profit -= charge_amount * 0.2

                elif command == "discharge_command":
                    discharge_amount = min(0.5, vehicle_soc_kwh)
                    vehicle_soc_kwh -= discharge_amount
                    vehicle_soc_kwh = max(0, vehicle_soc_kwh)
                    updated_soc = (vehicle_soc_kwh / battery_capacity_kwh) * 100

                    log(f"{vehicle_id} Boşaltıyor → -{discharge_amount:.2f} kWh → SoC: %{updated_soc:.2f}", "BOŞALTMA")

                    total_v2g_energy += discharge_amount

                    discharge_elem = ET.SubElement(root, "Discharge")
                    discharge_elem.set("vehicle_id", vehicle_id)
                    discharge_elem.set("amount_kWh", f"{discharge_amount:.2f}")
                    discharge_elem.set("new_soc_percent", f"{updated_soc:.2f}")
                    discharge_elem.set("time", f"{sim_time}")

                    mqtt_client.publish("evse/cmd", json.dumps({
                        "vehicle_id": vehicle_id,
                        "action": "v2g_discharge",
                        "amount_kWh": discharge_amount
                    }))

                    total_profit += discharge_amount * 0.3

                if time_in_charging > 150:
                    log(f"{vehicle_id} şarj süresi doldu, araç tekrar hareket ediyor.", "ÇIKIŞ")
                    info_elem = ET.SubElement(root, "Info")
                    info_elem.set("message", "Şarj istasyonunda bekleme süresi bitti, araç hareket ediyor.")
                    info_elem.set("time", f"{sim_time}")

                    traci.vehicle.setSpeed(vehicle_id, 5)
                    route = traci.vehicle.getRoute(vehicle_id)
                    current_edge = traci.vehicle.getRoadID(vehicle_id)
                    if current_edge in route:
                        current_index = route.index(current_edge)
                        if current_index + 1 < len(route):
                            next_edge = route[current_index + 1]
                            traci.vehicle.changeTarget(vehicle_id, next_edge)

                    at_charging_station = False
                    charging_completed = True

            # SoC kaydı
            soc_percent = (vehicle_soc_kwh / battery_capacity_kwh) * 100
            soc_history["times"].append(sim_time)
            soc_history["soc_percentages"].append(soc_percent)

        time.sleep(0.1)

except KeyboardInterrupt:
    log("Simülasyon kullanıcı tarafından durduruldu.", "KAPAT")

finally:
    traci.close()
    mqtt_client.loop_stop()
    mqtt_client.disconnect()
    log("MQTT bağlantısı kapatıldı.")

    co2_avoided = total_v2g_energy * CO2_AVOIDED_PER_KWH
    log(f"Toplam şebekeye aktarılan enerji: {total_v2g_energy:.2f} kWh", "RAPOR")
    log(f"Önlenen CO₂ salınımı: {co2_avoided:.2f} kg", "RAPOR")

    if len(root) > 0:
        tree = ET.ElementTree(root)
        tree.write("sonuclar.xml", encoding="utf-8", xml_declaration=True)
        log("Simülasyon sonuçları 'sonuclar.xml' dosyasına kaydedildi.")
    else:
        log("Kayıt edilecek veri bulunamadı, XML oluşturulmadı.", "UYARI")

    if soc_history["times"]:
        sim_times = soc_history["times"]
        soc_values = soc_history["soc_percentages"]
        sim_hours = [(initial_hour + int(t // 5)) % 24 for t in sim_times]
        hour_labels = [f"{h:02d}:00" for h in sim_hours]

        plt.figure(figsize=(14, 8))
        plt.plot(sim_times, soc_values, label=f"Araç {vehicle_id}", marker="o")
        plt.xlabel("Simülasyon Zamanı (saniye)")
        plt.ylabel("State of Charge (%)")
        plt.title("Araç SoC Değişimi")
        plt.grid(True)
        plt.legend()

        ax1 = plt.gca()
        ax2 = ax1.twiny()
        ax2.set_xlim(ax1.get_xlim())
        ax2.set_xticks(sim_times[::max(len(sim_times)//10, 1)])
        ax2.set_xticklabels(hour_labels[::max(len(hour_labels)//10, 1)], rotation=45)
        ax2.set_xlabel("Saat")

        plt.text(0.95, 0.05, f"Toplam Kar: {total_profit:.2f} TL", transform=plt.gca().transAxes,
                 fontsize=12, verticalalignment='bottom', horizontalalignment='right',
                 bbox=dict(facecolor='white', alpha=0.8))

        plt.text(0.95, 0.01, f"\u00d6nlenen CO₂: {co2_avoided:.2f} kg", transform=plt.gca().transAxes,
                 fontsize=12, verticalalignment='bottom', horizontalalignment='right',
                 bbox=dict(facecolor='white', alpha=0.8))

        plt.tight_layout()
        plt.show()
    else:
        log("Grafik çizimi için yeterli veri bulunamadı.", "UYARI")