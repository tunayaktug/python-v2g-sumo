# V2Gsumo
V2G (Vehicle-to-Grid) sistemleri için SUMO tabanlı bir simülasyon ve enerji yönetim sistemi modeli – şarj/deşarj optimizasyonu ve EMS karar desteği içerir.



Proje Hakkında

Bu proje, elektrikli araçların şebeke ile etkileşimini simüle etmek amacıyla geliştirilmiş bir V2G (Vehicle-to-Grid) sistem modelidir. SUMO (Simulation of Urban MObility) platformu kullanılarak trafik ve enerji etkileşimleri modellenmiş, bir EMS (Energy Management System) tarafından araçlara şarj/deşarj komutları verilmiştir.

Proje, araçların batarya durumlarına, enerji fiyatlarına ve saatlik enerji taleplerine göre karar verme algoritması ile çalışmaktadır. Ayrıca MQTT protokolü ile haberleşme sağlanmakta ve simülasyon sonuçları XML olarak kaydedilip görselleştirilmektedir.

⚙️ Kullanılan Teknolojiler ve Yapılar

SUMO: Gerçek zamanlı trafik simülasyonu

Python: Kontrol ve analiz kodları

MQTT (HiveMQ): Haberleşme protokolü

EMS Decision Model: Zaman-serili şarj/deşarj komutları

Tkinter GUI: Simülasyonu başlatmak ve sonuçları göstermek için kullanıcı arayüzü

📂 Proje İçeriği



├── arayuz.py               # Kullanıcı arayüzü (simülasyonu başlatır)
├── deneme.py               # Ana simülasyon yürütücüsü
├── ems_decision.py         # EMS karar algoritması
├── ems_trip_analysis.py    # Araç park süreleri analizi
├── ems_v2g_analysis.py     # Simülasyon sonucu analiz
├── ems_v2g_optimization.py # Enerji optimizasyonu
├── *.xml                   # SUMO ağ, araç ve rota tanımları
├── sonuclar.xml            # Simülasyon sonuçları (oluşur)


📊 Özellikler
Zaman bazlı enerji fiyatlandırması

Akıllı EMS karar sistemi (charge / discharge / idle)

CO₂ salınımı önleme ve kâr hesaplamaları

Optimizasyon destekli enerji tahsisi

Gerçek zamanlı simülasyon görselleştirmesi

👥 Geliştirici Notu


Bu proje, Eskişehir Osmangazi Üniversitesi bünyesinde gerçekleştirilmiş bir araştırma çalışmasıdır ve geleceğin akıllı şebeke altyapıları için temel bir örnek teşkil etmektedir.
