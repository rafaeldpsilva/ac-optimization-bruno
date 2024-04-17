from bson import ObjectId
from pymongo import MongoClient

from utils import utils


class DivisionRepository:
    def __init__(self):
        self.config = utils.get_config()
        self.server = str(self.config['storage']['local']['server'])
        self.port = str(self.config['storage']['local']['port'])
        self.DIVISIONS = self.config['storage']['local']['divisions']
        self.CONFIG = self.config['storage']['local']['config']

    def get_divisions(self):
        client = MongoClient(self.server + ':' + self.port)
        divisions = list(client[self.DIVISIONS[0]][self.DIVISIONS[1]].find())
        client.close()
        return divisions

    def get_division(self, id):
        client = MongoClient(self.server + ':' + self.port)
        division = list(client[self.DIVISIONS[0]][self.DIVISIONS[1]].find({"_id": ObjectId(id)}))
        client.close()
        return division[0]

    def insert_division(self, name, iots, ac_status_configuration):
        try:
            division_save = {"name": name, "iots": iots,
                             "ac_status_configuration": ac_status_configuration}
            client = MongoClient(self.server + ':' + self.port)
            client[self.DIVISIONS[0]][self.DIVISIONS[1]].insert_one(division_save)
        except Exception as e:
            print("An exception occurred ::", e)
        finally:
            client.close()

        if self.config['app']['monitoring']:
            print('\nDivision\n', division_save)

    def update_division(self, id, name, iots, ac_status_configuration):
        try:
            division_save = {'name': name, 'iots': iots,
                             "ac_status_configuration": ac_status_configuration}
            client = MongoClient(self.server + ':' + self.port)
            client[self.DIVISIONS[0]][self.DIVISIONS[1]].update_one({'_id': id}, {'$set': division_save})
        except Exception as e:
            print("An exception occurred ::", e)
        finally:
            client.close()

        if self.config['app']['monitoring']:
            print('\nUpdate Division', name, '\n', division_save)
