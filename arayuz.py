import tkinter as tk
from tkinter import messagebox, ttk
import subprocess
import xml.etree.ElementTree as ET
import threading
import time


def run_simulation(event=None):
    progress.start()
    start_button.config(state="disabled")

    def simulation_thread():
        try:
            messagebox.showinfo("Bilgi", "Simülasyon başlatılıyor...")
            subprocess.run(["python", "deneme.py"], check=True)
            # Simülasyon bittiğinde:
            progress.stop()
            progress.config(mode='determinate', maximum=100, value=100)
            start_button.config(state="normal")
            show_results()
        except subprocess.CalledProcessError:
            progress.stop()
            messagebox.showerror("Hata", "Simülasyon çalıştırılamadı.")
            start_button.config(state="normal")
        except FileNotFoundError:
            progress.stop()
            messagebox.showerror("Hata", "Simülasyon dosyası bulunamadı.")
            start_button.config(state="normal")

    threading.Thread(target=simulation_thread).start()


def show_results():
    try:
        tree = ET.parse("sonuclar.xml")
        root_xml = tree.getroot()

        result_window = tk.Toplevel(root)
        result_window.title("Simülasyon Sonuçları")
        result_window.geometry("1200x700")
        result_window.configure(bg="#ecf0f1")

        columns = ("Tip", "Araç ID", "SoC", "Komut/Fiyat", "Zaman", "Mesaj")
        treeview = ttk.Treeview(result_window, columns=columns, show="headings")
        treeview.pack(expand=True, fill="both", padx=20, pady=20)

        for col in columns:
            treeview.heading(col, text=col, command=lambda c=col: sort_by(treeview, c, False))
            treeview.column(col, anchor="center")

        style = ttk.Style()
        style.configure("Treeview", font=("Segoe UI", 12), rowheight=28)
        style.map("Treeview", background=[('selected', '#3498db')], foreground=[('selected', 'white')])

        treeview.tag_configure('charge', background='#d4efdf')
        treeview.tag_configure('discharge', background='#f5b7b1')
        treeview.tag_configure('arrival', background='#d6eaf8')
        treeview.tag_configure('info', background='#f9e79f')
        treeview.tag_configure('ems', background='#f2f4f4')

        for elem in root_xml:
            if elem.tag == "Arrival":
                data = ("GELİŞ", elem.get('vehicle_id'), f"%{elem.get('soc_percent')}", "", elem.get('time'), "")
                tag = 'arrival'
            elif elem.tag == "EMSDecision":
                data = ("EMS", elem.get('vehicle_id'), "", f"{elem.get('command')} / {elem.get('price')}", elem.get('time'), "")
                tag = 'ems'
            elif elem.tag == "Charge":
                data = ("ŞARJ", elem.get('vehicle_id'), f"%{elem.get('new_soc_percent')}", f"+{elem.get('amount_kWh')} kWh", elem.get('time'), "")
                tag = 'charge'
            elif elem.tag == "Discharge":
                data = ("DEŞARJ", elem.get('vehicle_id'), f"%{elem.get('new_soc_percent')}", f"-{elem.get('amount_kWh')} kWh", elem.get('time'), "")
                tag = 'discharge'
            elif elem.tag == "Info":
                data = ("BİLGİ", "", "", "", elem.get('time'), elem.get('message'))
                tag = 'info'
            else:
                data = (elem.tag, "", "", "", "", str(elem.attrib))
                tag = ''

            treeview.insert("", "end", values=data, tags=(tag,))
    except FileNotFoundError:
        messagebox.showerror("Hata", "Veri dosyası (XML) bulunamadı.")
    except ET.ParseError:
        messagebox.showerror("Hata", "XML dosyası bozuk veya okunamadı.")

def sort_by(treeview, col, descending):
    data_list = [(treeview.set(child, col), child) for child in treeview.get_children('')]
    try:
        data_list.sort(key=lambda t: float(t[0].replace("%", "").replace("+", "").replace("-", "").split()[0]), reverse=descending)
    except ValueError:
        data_list.sort(reverse=descending)
    for index, (val, child) in enumerate(data_list):
        treeview.move(child, '', index)
    treeview.heading(col, command=lambda: sort_by(treeview, col, not descending))

root = tk.Tk()
root.title("V2G SUMO PROJESİ")
root.state('zoomed')
root.configure(bg="#1a3a5e")  # Koyu lacivert

# === Başlık (Gölge efekti) ===
shadow_label = tk.Label(root, text="V2G SUMO PROJESİ", font=("Helvetica", 36, "bold"),
                        fg="black", bg="#1a3a5e")
shadow_label.place(relx=0.502, rely=0.173, anchor="center")

title_label = tk.Label(root, text="V2G SUMO PROJESİ", font=("Helvetica", 36, "bold"),
                       fg="white", bg="#1a3a5e")
title_label.place(relx=0.5, rely=0.17, anchor="center")

# === Buton ===
def on_enter(event): start_button.config(bg="#1f618d")
def on_leave(event): start_button.config(bg="#3498db")

start_button = tk.Button(
    root,
    text="▶ Simülasyonu Başlat",
    font=("Segoe UI", 18, "bold"),
    width=25,
    height=2,
    bg="#3498db",
    fg="white",
    activebackground="#1f618d",
    activeforeground="white",
    bd=0,
    relief="flat",
    cursor="hand2",
    command=run_simulation
)
start_button.place(relx=0.5, rely=0.5, anchor="center")
start_button.bind("<Enter>", on_enter)
start_button.bind("<Leave>", on_leave)

# === Progress Bar ===
progress = ttk.Progressbar(root, mode='indeterminate', length=300)
progress.place(relx=0.5, rely=0.57, anchor="center")


# === Footer ===
footer_label = tk.Label(root, text="Eskişehir Osmangazi Üniversitesi V2G SUMO projesi 2025",
                        font=("Segoe UI", 12), bg="#154360", fg="white", padx=10, pady=5)
footer_label.place(relx=0.5, rely=0.96, anchor="center")

root.mainloop()
