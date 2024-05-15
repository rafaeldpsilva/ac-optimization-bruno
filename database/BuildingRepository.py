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