# V2Gsumo
A SUMO-based simulation and energy management system model for V2G (Vehicle-to-Grid) systems – includes charge/discharge optimization and EMS decision support.



## 🚗 Overview
This project simulates **Vehicle-to-Grid (V2G)** interactions using the **SUMO** traffic simulator integrated with a custom-developed **Energy Management System (EMS)**. Electric vehicles (EVs) communicate with a centralized EMS via **MQTT**, receiving commands to charge or discharge based on battery status, time-of-day electricity prices, and energy demand.

An intuitive **Tkinter-based GUI** is used to start the simulation and display real-time results from the generated XML logs. The system incorporates optimization logic and environmental impact metrics (e.g., CO₂ savings).

## 🔧 Core Technologies
- 🛣️ **SUMO** (Simulation of Urban MObility) for traffic modeling
- ⚡ **EMS Logic** (`ems_decision.py`) – decision engine based on SoC, price, demand
- 🧠 **Optimization** – using linear programming (`scipy.optimize.linprog`)
- 🛰️ **MQTT** (HiveMQ) for real-time message exchange
- 📊 **Tkinter GUI** for running and visualizing simulations
- 📈 **Matplotlib & Pandas** for analysis and graphing

## 📂 File Structure
├── arayuz.py # GUI: Start sim + show results
├── deneme.py # Main simulation logic
├── ems_decision.py # EMS: charge/discharge decisions
├── ems_v2g_analysis.py # Analysis of V2G performance
├── ems_trip_analysis.py # Vehicle trip and parking durations
├── ems_v2g_optimization.py # Optimization for energy distribution
├── *.xml # SUMO network, route, vehicle & grid configs
├── sonuclar.xml # Generated simulation results (XML)



## 📊 Simulation Features
- Time-based electricity price profile
- SoC-class-based decision rules (critical, low, medium, high)
- Bidirectional energy flow: grid ↔ vehicle
- Environmental metrics: total V2G energy, avoided CO₂ (kg)
- Dynamic visualization of SoC and profit in simulation runtime

## 📊 Sample Output (Graph)
- Vehicle SoC (%) over simulation time
- Optimized charge/discharge distribution by hour
- CO₂ savings and total profit annotation on plot

## 👥 Developer Note
This work is developed under the academic scope of **Eskişehir Osmangazi University** and aims to demonstrate smart grid readiness with intelligent EV-grid coordination systems.





