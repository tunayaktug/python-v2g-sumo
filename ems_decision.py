class EMSDecision:
    def __init__(self):
        self.state = 'Idle'
        self.last_command = None
        self.price_profile = [
            15.0, 14.0, 13.5, 13.0, 12.5, 12.0, 12.5, 13.0,
            20.0, 25.0, 28.0, 30.0, 28.0, 26.0, 25.0, 22.0,
            26.0, 28.0, 27.0, 24.0, 21.0, 18.0, 16.0, 15.0
        ]

    def get_price(self, hour):
        return self.price_profile[hour % 24]

    def get_demand(self, hour):
        if 0 <= hour < 6:
            return "low"
        elif 6 <= hour < 18:
            return "medium"
        else:
            return "high"

    def classify_soc(self, soc_percent):
        if soc_percent < 10:
            return 'critical_low'
        elif soc_percent < 25:
            return 'very_low'
        elif soc_percent < 40:
            return 'low'
        elif soc_percent < 60:
            return 'medium'
        elif soc_percent < 80:
            return 'high'
        else:
            return 'very_high'

    def cfg_decision(self, soc_percent, hour):
        soc_class = self.classify_soc(soc_percent)
        price = self.get_price(hour)
        demand = self.get_demand(hour)

        if soc_class in ['critical_low', 'very_low']:
            return 'charge_command', price

        if soc_class == 'low':
            if price < 18.0:
                return 'charge_command', price
            else:
                return 'no_action', price

        if soc_class == 'medium':
            if price >= 26.0 and demand == 'high':
                return 'discharge_command', price
            elif price <= 14.0 and demand == 'low':
                return 'charge_command', price
            else:
                return 'no_action', price

        if soc_class == 'high':
            if price >= 28.0:
                return 'discharge_command', price
            elif price <= 13.0 and demand == 'low':
                return 'charge_command', price
            else:
                return 'no_action', price

        if soc_class == 'very_high':
            if price >= 24.0:
                return 'discharge_command', price
            else:
                return 'no_action', price

        return 'no_action', price


    def dfa_transition(self, command):
        # Durum geçişi: discharge ve charge arasında aniden geçişi önler
        if self.state == 'Idle':
            if command == 'charge_command':
                self.state = 'Charging'
            elif command == 'discharge_command':
                self.state = 'Discharging'

        elif self.state == 'Charging':
            if command == 'discharge_command':
                self.state = 'Idle'
            elif command == 'no_action':
                self.state = 'Idle'

        elif self.state == 'Discharging':
            if command == 'charge_command':
                self.state = 'Idle'
            elif command == 'no_action':
                self.state = 'Idle'

        return self.state

    def decide(self, soc_percent, vehicle_count, hour):
        command, price = self.cfg_decision(soc_percent, hour)
        new_state = self.dfa_transition(command)
        demand = self.get_demand(hour)
        self.last_command = command
        return price, demand, command, new_state
