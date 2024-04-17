from datetime import datetime, timedelta

from pymongo import MongoClient

from utils import utils


class BatteryRepository:
    def __init__(self):
        self.config = utils.get_config()
        self.server = str(self.config['storage']['local']['server'])
        self.port = str(self.config['storage']['local']['port'])
        self.BATTERIES = self.config['storage']['local']['batteries']

    def get_batteries(self):
        batteries = []
        for battery in self.config['resources']['batteries']:
            batteries.append({'name': battery['name'], 'ip': battery['ip'], 'capacity': battery['capacity']})
        return batteries

    def get_batteries_historic(self, start):
        client = MongoClient(self.server + ':' + self.port)
        historic = list(client[self.BATTERIES[0]][self.BATTERIES[1]].find(
            {'datetime': {'$gt': datetime.strptime(start, "%Y-%m-%d %H:%M:%S")}}))
        client.close()
        return historic

    def insert_batteries(self, batteries):
        try:
            batteries_save = {"batteries": batteries,
                              "datetime": datetime.now() + timedelta(hours=self.config['app']['hour_offset'])}
            client = MongoClient(self.server + ':' + self.port)
            client[self.BATTERIES[0]][self.BATTERIES[1]].insert_one(batteries_save)
        except Exception as e:
            print("An exception occurred ::", e)
        finally:
            client.close()

        if self.config['app']['monitoring']:
            print('\nBatteries\n', batteries_save)
