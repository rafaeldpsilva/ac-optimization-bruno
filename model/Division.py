import pandas as pd

from database.DivisionRepository import DivisionRepository
from modules import ACStatusAdapter


class Division:
    def __init__(self, name, iots, id="", ac_status_configuration=""):
        self.name = name
        self.iots = iots
        self.id = id
        self.ac_status_configuration = ac_status_configuration

    def get_ac_status(self, iot_readings_historic):
        considered_iots = [self.ac_status_configuration['outside_temperature'],
                           self.ac_status_configuration['temperature'], self.ac_status_configuration['humidity'],
                           self.ac_status_configuration['light']]
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
            columns={self.ac_status_configuration['outside_temperature'] + "_temperature": 'Outside temperature (ºC)',
                     self.ac_status_configuration['temperature'] + "_temperature": 'Temperature (Cº)',
                     self.ac_status_configuration['humidity'] + "_humidity": 'Humidity (%)',
                     self.ac_status_configuration['light'] + "_light": 'Light (%)'},
            inplace=True)

        aux['Temperature (Cº)'] = aux['Temperature (Cº)'] / 10
        aux['Humidity (%)'] = aux['Humidity (%)'] / 10
        aux['Light (%)'] = aux['Light (%)'] / 10
        aux['Heat Index (ºC)'] = ACStatusAdapter.calculate_heat_index_custom_celsius(aux['Temperature (Cº)'],
                                                                                     aux['Humidity (%)'])
        aux['Outside temperature (ºC)'] = aux['Temperature (Cº)'] - 4

        # Talvez calcular media
        return ACStatusAdapter.predict_ac_status(aux.tail(1)['Outside temperature (ºC)'],
                                                 aux.tail(1)['Temperature (Cº)'], aux.tail(1)['Heat Index (ºC)'],
                                                 aux.tail(1)['Light (%)'])

    def save(self):
        division_repo = DivisionRepository()
        return division_repo.insert_division(self.name, self.iots, self.ac_status_configuration)

    def update(self, name, iots, ac_status_configuration):
        division_repo = DivisionRepository()
        division_repo.update_division(self.id, name, iots, ac_status_configuration)

    def configure_ac_status_model(self, ac_status_configuration):
        if ac_status_configuration['outside_temperature'] and ac_status_configuration['temperature'] and \
                ac_status_configuration['humidity'] and ac_status_configuration['light']:
            self.ac_status_configuration = ac_status_configuration

    def to_json(self):
        return {"id": self.id, "name": self.name, "iots": self.iots,
                "ac_status_configuration": self.ac_status_configuration}
