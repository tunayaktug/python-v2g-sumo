import tkinter as tk
from tkinter import messagebox
import subprocess
import xml.etree.ElementTree as ET

def run_simulation():
    try:
        messagebox.showinfo("Bilgi", "Simülasyon başlatılıyor...")
        sumo_command = ["python", "deneme.py"]
        subprocess.run(sumo_command, check=True)
        show_results()

    except subprocess.CalledProcessError:
        messagebox.showerror("Hata", "Simülasyon çalıştırılamadı.")
    except FileNotFoundError:
        messagebox.showerror("Hata", "Simülasyon dosyası bulunamadı.")

def show_results():
    try:
        tree = ET.parse("sonuclar.xml")
        root_xml = tree.getroot()

        result_window = tk.Toplevel(root)
        result_window.title("Simülasyon Sonuçları")
        text = tk.Text(result_window, wrap="word")
        text.pack(expand=True, fill="both")

        for elem in root_xml:
            if elem.tag == "Arrival":
                line = f"[GELİŞ] Araç ID: {elem.get('vehicle_id')} SoC: %{elem.get('soc_percent')} | Zaman: {elem.get('time')}\n"
            elif elem.tag == "EMSDecision":
                line = f"[EMS] Araç ID: {elem.get('vehicle_id')} | Komut: {elem.get('command')} | Fiyat: {elem.get('price')} | Zaman: {elem.get('time')}\n"
            elif elem.tag == "Charge":
                line = f"[ŞARJ] Araç ID: {elem.get('vehicle_id')} +{elem.get('amount_kWh')} kWh | Yeni SoC: %{elem.get('new_soc_percent')} | Zaman: {elem.get('time')}\n"
            elif elem.tag == "Discharge":
                line = f"[DEŞARJ] Araç ID: {elem.get('vehicle_id')} -{elem.get('amount_kWh')} kWh | Yeni SoC: %{elem.get('new_soc_percent')} | Zaman: {elem.get('time')}\n"
            elif elem.tag == "Info":
                line = f"[BİLGİ] {elem.get('message')} | Zaman: {elem.get('time')}\n"
            else:
                line = f"[{elem.tag}] {elem.attrib}\n"

            text.insert("end", line)

    except FileNotFoundError:
        messagebox.showerror("Hata", "Veri dosyası (XML) bulunamadı.")
    except ET.ParseError:
        messagebox.showerror("Hata", "XML dosyası bozuk veya okunamadı.")

root = tk.Tk()
root.title("SUMO V2G Simülasyonu")

start_button = tk.Button(root, text="Simülasyonu Başlat", command=run_simulation, height=2, width=20)
start_button.pack(pady=30)

root.mainloop()
