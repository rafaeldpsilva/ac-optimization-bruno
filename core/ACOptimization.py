import time
from threading import Thread
from datetime import datetime, timedelta
import pandas as pd
import csv
import schedule
import requests
from model.Division import Division
from modules import ACStatusAdapter2
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

    def save_state(self, decision, outside_temp, temp, humidity, heat_index, occupation):
        now = datetime.now()
        current_time = now.strftime("%Y-%m-%d %H:%M:%S")
        data = [current_time, decision, outside_temp, temp, humidity, heat_index, occupation]

        csv_file = "decisions.csv"

        try:
            with open(csv_file, mode='a', newline='') as file:
                writer = csv.writer(file)
                writer.writerow(data)
            print("Decision saved to CSV successfully.")
        except Exception as e:
            print(f"Error saving decision to CSV: {e}")

    def save_optimization(self, decision):
        now = datetime.now()
        current_time = now.strftime("%Y-%m-%d %H:%M:%S")
        data = [current_time, decision]

        csv_file = "sent_actions.csv"

        try:
            with open(csv_file, mode='a', newline='') as file:
                writer = csv.writer(file)
                writer.writerow(data)
            print("Decision saved to CSV successfully.")
        except Exception as e:
            print(f"Error saving decision to CSV: {e}")

    def send_off(self):
        print("Sending Off")
        self.save_optimization("off")
        url = "http://homeassistant.local:8123/api/services/script/turn_off_102"
        headers = {
            "Authorization": "Bearer eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJpc3MiOiI3YzZhOTQ0YjBhYmE0ZGQ0YTNlY2Q4M2RhYWRmZDY1NyIsImlhdCI6MTcxMzM1MDIyMSwiZXhwIjoyMDI4NzEwMjIxfQ.Au0zNGmNSEmpCZyIMzooQIBZNZ5npY6Cjp-m7eHN0_s",
            "Content-Type": "application/json"
        }
        data = '{"entity_id": "script.turn_off_102"}'

        try:
            response = requests.post(url, headers=headers, data=data)
            response.raise_for_status()  # Raise an exception for 4xx or 5xx status codes
            print("Request successful!")
            print("Response:", response.text)
        except requests.exceptions.RequestException as e:
            print("Request failed:", e)  

    def send_cold(self):
        print("Sending Cold")
        self.save_optimization("cold")
        url = "http://homeassistant.local:8123/api/services/script/cold_102"
        headers = {
            "Authorization": "Bearer eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJpc3MiOiI3YzZhOTQ0YjBhYmE0ZGQ0YTNlY2Q4M2RhYWRmZDY1NyIsImlhdCI6MTcxMzM1MDIyMSwiZXhwIjoyMDI4NzEwMjIxfQ.Au0zNGmNSEmpCZyIMzooQIBZNZ5npY6Cjp-m7eHN0_s",
            "Content-Type": "application/json"
        }
        data = '{"entity_id": "script.cold_102"}'

        try:
            response = requests.post(url, headers=headers, data=data)
            response.raise_for_status()  # Raise an exception for 4xx or 5xx status codes
            print("Request successful!")
            print("Response:", response.text)
        except requests.exceptions.RequestException as e:
            print("Request failed:", e)
    
    def send_warm(self):
        print("Sending Warm")
        self.save_optimization("warm")
        url = "http://homeassistant.local:8123/api/services/script/warm_102"
        headers = {
            "Authorization": "Bearer eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJpc3MiOiI3YzZhOTQ0YjBhYmE0ZGQ0YTNlY2Q4M2RhYWRmZDY1NyIsImlhdCI6MTcxMzM1MDIyMSwiZXhwIjoyMDI4NzEwMjIxfQ.Au0zNGmNSEmpCZyIMzooQIBZNZ5npY6Cjp-m7eHN0_s",
            "Content-Type": "application/json"
        }
        data = '{"entity_id": "script.warm_102"}'

        try:
            response = requests.post(url, headers=headers, data=data)
            response.raise_for_status()  # Raise an exception for 4xx or 5xx status codes
            print("Request successful!")
            print("Response:", response.text)
        except requests.exceptions.RequestException as e:
            print("Request failed:", e)
    
    def get_iot_readings(self):
        building_repo = BuildingRepository()
        iots = building_repo.get_historic_iots(datetime.now() - timedelta(hours=1))
        iot_readings_historic = pd.DataFrame(iots)
        iot_readings_historic = iot_readings_historic.drop("_id", axis=1)
        return iot_readings_historic

    def predict_ac_status(self):
        iot_readings_historic = self.get_iot_readings()
        
        considered_iots = ["Lamp 1_102","Lamp 2_102","Weather","Temperature Sensor 102","Humidity Sensor 102","Light Sensor 102","Air Conditioner 102"]
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
            columns={"Weather" + "_temperature": 'Outside temperature (ºC)',
                    "Temperature Sensor 102" + "_temperature": 'Temperature (Cº)',
                        "Humidity Sensor 102" + "_humidity": 'Humidity (%)',
                        "Light Sensor 102" + "_light": 'Light (%)',
                        "Lamp 1_102_power": 'Lamp 1',
                        "Lamp 2_102_power": 'Lamp 2'},
            inplace=True)
        aux = aux.values.tolist()
        aux = pd.DataFrame(aux,columns=['Air Conditioner_power','Air Conditioner_voltage','Air Conditioner_current','Lamp 1','Lamp 2','Temperature (Cº)','Humidity (%)','Light (%)','Outside temperature (ºC)'])
        aux['AC status'] = aux.apply(lambda x: 0 if x['Air Conditioner_power'] == 0 else 1, axis=1)
        aux['Outside temperature (ºC)'] = aux.apply(lambda x: x['Outside temperature (ºC)']*10, axis=1)
        aux['Occupation'] = aux.apply(lambda x: 0 if x['Lamp 1'] and x['Lamp 2'] == 0 else 1, axis=1)
        aux = aux.drop(["Air Conditioner_power","Air Conditioner_voltage","Air Conditioner_current","Lamp 1","Lamp 2"], axis=1)
        aux['Heat Index (ºC)'] = ACStatusAdapter2.calculate_heat_index_custom_celsius(aux['Temperature (Cº)'], aux['Humidity (%)'])

        # Talvez calcular media
        new_status = ACStatusAdapter2.predict_ac_status(aux.tail(1).iloc[0]['Outside temperature (ºC)'],
                                                 aux.tail(1).iloc[0]['Temperature (Cº)'], aux.tail(1).iloc[0]['Humidity (%)'],aux.tail(1).iloc[0]['Heat Index (ºC)'],
                                                 aux.tail(1).iloc[0]['Occupation'])
        
        if new_status == 1:
            new_status = "on-cold"
        elif new_status == -1:
            new_status = "on-warm"
        else:
            new_status = "off"
            
        if new_status != self.ac_status:
            if new_status == "on-cold":
                self.ac_status = new_status
                self.send_cold()
            elif new_status == "on-warm":
                self.ac_status = new_status
                self.send_warm()
            else:
                self.ac_status = new_status
                self.send_off()
        
        self.save_state(self.ac_status, aux.tail(1).iloc[0]['Outside temperature (ºC)'], aux.tail(1).iloc[0]['Temperature (Cº)'], aux.tail(1).iloc[0]['Humidity (%)'],aux.tail(1).iloc[0]['Heat Index (ºC)'],aux.tail(1).iloc[0]['Occupation'])
        print("AC STATUS", self.ac_status, 
              "outside temp", aux.tail(1).iloc[0]['Outside temperature (ºC)'], 
              "temp", aux.tail(1).iloc[0]['Temperature (Cº)'], 
              "Humidity", aux.tail(1).iloc[0]['Humidity (%)'],
              "heat index", aux.tail(1).iloc[0]['Heat Index (ºC)'],
              "occupation", aux.tail(1).iloc[0]['Occupation'])
        return self.ac_status

    def run(self):
        #set_right_time = True
        #while set_right_time:
        #    minutes = datetime.now().minute
        #    if minutes == 0 or minutes == 15 or minutes == 30 or minutes == 45:
        #        set_right_time = False
        #    time.sleep(1)

        schedule.every(15).minutes.do(self.predict_ac_status)
        #schedule.every(2).minutes.do(self.send_actions)

        self.predict_ac_status()
        #self.send_actions()
        while True:
            schedule.run_pending()
            time.sleep(1)