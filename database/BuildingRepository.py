from datetime import datetime

from pymongo import MongoClient, DESCENDING

from utils import utils


class BuildingRepository:
    def __init__(self):
        self.config = utils.get_config()
        self.server = str(self.config['storage']['local']['server'])
        self.port = str(self.config['storage']['local']['port'])
        self.IOTS_READING = self.config['storage']['local']['iots_reading']
        self.FORECAST = self.config['storage']['local']['forecast']
        self.TOTALPOWER = self.config['storage']['local']['totalpower']
        self.TOTALPOWERHOUR = self.config['storage']['local']['totalpowerhour']
        self.CONFIG_DB = self.config['storage']['local']['config']

    def save_config(self):
        try:
            conf = {"config": "config", "auto_answer": True}
            client = MongoClient(self.server + ':' + self.port)
            client[self.CONFIG_DB[0]][self.CONFIG_DB[1]].insert_one(conf)
        except Exception as e:
            print("An exception occurred ::", e)
        finally:
            client.close()

        if self.config['app']['monitoring']:
            print('\nConfig\n', conf)

    def get_historic_interval_iots(self, start, end):
        client = MongoClient(self.server + ':' + self.port)
        historic = list(
            client[self.IOTS_READING[0]][self.IOTS_READING[1]].find({'datetime': {'$gt': start, '$lt': end}}))
        client.close()
        return historic

    def get_historic_iots(self, start):
        if type(start) is str:
            date_start = datetime.strptime(start, "%Y-%m-%d %H:%M:%S")
        else:
            date_start = start
        client = MongoClient(self.server + ':' + self.port)
        historic = list(client[self.IOTS_READING[0]][self.IOTS_READING[1]].find(
            {'datetime': {'$gt': date_start}}))
        client.close()
        return historic

    def get_historic_hour(self, start):
        if type(start) is str:
            date_start = datetime.strptime(start, "%Y-%m-%d %H:%M:%S")
        else:
            date_start = start
        client = MongoClient(self.server + ':' + self.port)
        historic = list(client[self.TOTALPOWERHOUR[0]][self.TOTALPOWERHOUR[1]].find({'datetime': {'$gt': date_start}}))
        client.close()
        return historic
    
    def get_historic_hour_interval(self, start: datetime, end: datetime):
        client = MongoClient(self.server + ':' + self.port)
        historic = list(client[self.TOTALPOWERHOUR[0]][self.TOTALPOWERHOUR[1]].find({'datetime': {'$gt': start, '$lt': end}}))
        client.close()
        return historic

    def iots_historic_update(self, start):
        client = MongoClient(self.server + ':' + self.port)
        historic = list(client[self.IOTS_READING[0]][self.IOTS_READING[1]].find({'datetime': {'$gt': start}}))
        client.close()
        client = MongoClient(self.server + ':' + self.port)
        for entry in historic:
            new_date = datetime.strptime(entry['datetime'], "%Y-%m-%d %H:%M:%S.%f")
            client[self.IOTS_READING[0]][self.IOTS_READING[1]].update_one({'datetime': entry['datetime']},
                                                                          {'$set': {'datetime': new_date}})

        client.close()
        return historic

    def get_iots_reading_col(self, time, time_emb):
        client = MongoClient(self.server + ':' + self.port)
        building_iot_reading = list(
            client[self.IOTS_READING[0]][self.IOTS_READING[1]].find({'datetime': {'$gt': time, '$lt': time_emb}}))
        client.close()
        return building_iot_reading

    def get_forecastvalue_col(self):
        client = MongoClient(self.server + ':' + self.port)
        forecastvalue = list(client.ForecastDay.forecastvalue.find().sort("_id", DESCENDING).limit(1))
        client.close()
        return forecastvalue

    def get_power_historic(self, start):
        client = MongoClient(self.server + ':' + self.port)
        building_totalpower = list(client[self.TOTALPOWER[0]][self.TOTALPOWER[1]].find({'datetime': {'$gt': start}}))
        client.close()
        return building_totalpower

    def get_power_historic_interval(self, start: datetime, end: datetime):
        client = MongoClient(self.server + ':' + self.port)
        building_totalpower = list(
            client[self.TOTALPOWER[0]][self.TOTALPOWER[1]].find({'datetime': {'$gt': start, '$lt': end}}))
        client.close()
        return building_totalpower

    def get_totalpower_col(self):
        client = MongoClient(self.server + ':' + self.port)
        building_totalpower = list(
            client[self.TOTALPOWER[0]][self.TOTALPOWER[1]].find().sort("datetime", -1).limit(100000))
        client.close()
        return building_totalpower

    def insert_total(self, totalpower, totalgeneration, datetime):
        try:
            total = {"totalpower": totalpower, "totalgeneration": totalgeneration, "datetime": datetime}
            client = MongoClient(self.server + ':' + self.port)
            client[self.TOTALPOWER[0]][self.TOTALPOWER[1]].insert_one(total)
        except Exception as e:
            print("An exception occurred ::", e)
        finally:
            client.close()

        if self.config['app']['monitoring']:
            print('\nTotal\n', total)

    def insert_forecast(self, forecast_power, datetime):
        try:
            forecast = {"forecast_power": forecast_power, "datetime": datetime}
            client = MongoClient(self.server + ':' + self.port)
            client[self.FORECAST[0]][self.FORECAST[1]].insert_one(forecast)
        except Exception as e:
            print("An exception occurred ::", e)
        finally:
            client.close()

        if self.config['app']['monitoring']:
            print('\nForecast\n', forecast)

    def insert_forecastday(self, iat, datetime):
        try:
            forecastday = {"forecast_power": {"0": str(iat[0, 0]),
                                              "1": str(iat[1, 0]),
                                              "2": str(iat[2, 0]),
                                              "3": str(iat[3, 0]),
                                              "4": str(iat[4, 0]),
                                              "5": str(iat[5, 0]),
                                              "6": str(iat[6, 0]),
                                              "7": str(iat[7, 0]),
                                              "8": str(iat[8, 0]),
                                              "9": str(iat[9, 0]),
                                              "10": str(iat[10, 0]),
                                              "11": str(iat[11, 0]),
                                              "12": str(iat[12, 0]),
                                              "13": str(iat[13, 0]),
                                              "14": str(iat[14, 0]),
                                              "15": str(iat[15, 0]),
                                              "16": str(iat[16, 0]),
                                              "17": str(iat[17, 0]),
                                              "18": str(iat[18, 0]),
                                              "19": str(iat[19, 0]),
                                              "20": str(iat[20, 0]),
                                              "21": str(iat[21, 0]),
                                              "22": str(iat[22, 0]),
                                              "23": str(iat[23, 0])},
                           "datetime": datetime}
            client = MongoClient(self.server + ':' + self.port)
            client.ForecastDay.forecastvalue.insert_one(forecastday)
        except Exception as e:
            print("An exception occurred ::", e)
        finally:
            client.close()

        if self.config['app']['monitoring']:
            print('\nForecastDay\n', forecastday)

    def insert_hour(self, start_hour, consumption, generation, flexibility):
        try:
            total = {"datetime": start_hour, "consumption": consumption, "generation": generation,
                     "flexibility": flexibility}
            client = MongoClient(self.server + ':' + self.port)
            client[self.TOTALPOWERHOUR[0]][self.TOTALPOWERHOUR[1]].insert_one(total)
        except Exception as e:
            print("An exception occurred ::", e)
        finally:
            client.close()

        if self.config['app']['monitoring']:
            print('\nTotal\n', total)
