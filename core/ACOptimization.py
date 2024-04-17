import time
from threading import Thread
from datetime import datetime, timedelta
import pandas as pd
import schedule

from model.Division import Division
from modules import ACStatusAdapter
from database.BuildingRepository import BuildingRepository

class ACOptimization(Thread):
    def __init__(self):
        self.id = id
        Thread.__init__(self)
        div = {
            "_id": {
                "$oid": "6568ac369c7e7bc486d7d110"
            },
            "name": "102",
            "iots": [
                "Air Conditioner 102",
                "Sockets-101-102-103",
                "Lamp 1_102",
                "Lamp 2_102",
                "Movement Sensor 102_1",
                "Movement Sensor 102_2",
                "Movement Sensor 102_3",
                "Door Sensor 102",
                "CO2 Sensor 102",
                "VOC Sensor 102",
                "Temperature Sensor 102",
                "Humidity Sensor 102",
                "Light Sensor 102",
                "Weather"
            ],
            "ac_status_configuration": {
                "outside_temperature": "Weather",
                "temperature": "Temperature Sensor 102",
                "humidity": "Humidity Sensor 102",
                "light": "Light Sensor 102"
            }
        }
        self.division = Division(div['name'], div['iots'], div['_id'], div['ac_status_configuration'])
        self.ac_status = ""

    def get_optimization(self):
        if self.ac_status != "":
            return self.ac_status
        else:
            self.predict_ac_status()
            return self.ac_status

    def save_optimization(self):
        pass

    def send_off(self):
        print("Sending Off")

    def send_cold(self):
        print("Sending Cold")
    
    def send_warm(self):
        print("Sending Warm")
    
    def get_iot_readings(self):
        building_repo = BuildingRepository()
        iots = building_repo.get_historic_iots(datetime.now() - timedelta(hours=1))
        iot_readings_historic = pd.DataFrame(iots)
        iot_readings_historic = iot_readings_historic.drop("_id", axis=1)
        return iot_readings_historic

    def predict_ac_status(self):
        iot_readings_historic = self.get_iot_readings()
        
        considered_iots = [self.division.ac_status_configuration['outside_temperature'],
                           self.division.ac_status_configuration['temperature'], self.division.ac_status_configuration['humidity'],
                           self.division.ac_status_configuration['light']]
        aux = pd.DataFrame()
        for i, row in iot_readings_historic.iterrows():
            new = pd.DataFrame()
            for iot in row['iots']:
                if iot['name'] in considered_iots:
                    for value in iot['values']:
                        val = value['values']
                        new[iot['name'] + '_' + value['type']] = [val]

            aux = pd.concat([aux, new])

        aux.rename(
            columns={self.division.ac_status_configuration['outside_temperature'] + "_temperature": 'Outside temperature (ºC)',
                     self.division.ac_status_configuration['temperature'] + "_temperature": 'Temperature (Cº)',
                     self.division.ac_status_configuration['humidity'] + "_humidity": 'Humidity (%)',
                     self.division.ac_status_configuration['light'] + "_light": 'Light (%)'},
            inplace=True)

        aux['Temperature (Cº)'] = aux['Temperature (Cº)'] / 10
        aux['Humidity (%)'] = aux['Humidity (%)'] / 10
        aux['Light (%)'] = aux['Light (%)'] / 10
        aux['Heat Index (ºC)'] = ACStatusAdapter.calculate_heat_index_custom_celsius(aux['Temperature (Cº)'],
                                                                                     aux['Humidity (%)'])
        aux['Outside temperature (ºC)'] = aux['Temperature (Cº)'] - 4

        # Talvez calcular media
        new_status = ACStatusAdapter.predict_ac_status(aux.tail(1).iloc[0]['Outside temperature (ºC)'],
                                                 aux.tail(1).iloc[0]['Temperature (Cº)'], aux.tail(1).iloc[0]['Heat Index (ºC)'],
                                                 aux.tail(1).iloc[0]['Light (%)'])
        
        if new_status == 1:
            self.ac_status = "on-cold"
            self.send_cold()
        elif new_status == -1:
            self.ac_status = "on-warm"
            self.send_warm()
        else:
            self.ac_status = "off"
            self.send_off()
            
        print("AC STATUS", self.ac_status)
        return self.ac_status

    def run(self):
        #set_right_time = True
        #while set_right_time:
        #    minutes = datetime.now().minute
        #    if minutes == 0 or minutes == 15 or minutes == 30 or minutes == 45:
        #        set_right_time = False
        #    time.sleep(1)

        schedule.every(2).minutes.do(self.predict_ac_status)
        #schedule.every(2).minutes.do(self.send_actions)

        self.predict_ac_status()
        #self.send_actions()
        while True:
            schedule.run_pending()
            time.sleep(1)