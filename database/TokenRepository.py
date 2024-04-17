from pymongo import MongoClient

from utils import utils


class TokenRepository:
    def __init__(self):
        self.config = utils.get_config()

        self.server = str(self.config['storage']['local']['server'])
        self.port = str(self.config['storage']['local']['port'])

        # criar a tabela
        self.TOKEN = self.config['storage']['local']['token']

    def client(self):
        return MongoClient(self.server + ':' + self.port)

    def get_tokens(self):
        client = MongoClient(self.server + ':' + self.port)
        tokenscol = list(client[self.TOKEN[0]][self.TOKEN[1]].find())
        client.close()
        return tokenscol

    def check_token(self, token):
        client = MongoClient(self.server + ':' + self.port)
        tokenscol = list(client[self.TOKEN[0]][self.TOKEN[1]].find({'token': token}))
        client.close()
        return tokenscol

    def revoke_token(self, token):
        client = MongoClient(self.server + ':' + self.port)
        tokenscol = client[self.TOKEN[0]][self.TOKEN[1]].update_one({'token': token}, {'$set': {'active': False}})
        client.close()
        return tokenscol

    def insert_token(self, token, datetime):
        try:
            token = {"token": token,
                     "datetime": datetime,
                     "active": True}
            client = MongoClient(self.server + ':' + self.port)
            client[self.TOKEN[0]][self.TOKEN[1]].insert_one(token)
        except Exception as e:
            print("An exception occurred ::", e)
        finally:
            client.close()

        if self.config['app']['monitoring']:
            print('\nToken\n', token)
        return token
