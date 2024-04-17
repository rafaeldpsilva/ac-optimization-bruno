from threading import Thread
from time import time, sleep

from modules import BatteryCommunicationAdapter
from utils import utils


class Battery(Thread):
    def __init__(self, config, config_monitoring):
        Thread.__init__(self)
        self.name = config["name"]
        self.ip = config["ip"]
        self.values = config["values"]
        self.monitoring_period = config_monitoring
        # print(self.name, self.values) # [{type:, tag:, dataType:},{type:, tag:, dataType:}]

    def get_battery_charging_rate(self):
        return BatteryCommunicationAdapter.get_battery_charging_rate(self.ip)

    def get_charge_state(self):
        return BatteryCommunicationAdapter.get_battery_state_of_charge(self.ip)

    def charge_battery(self, charge):
        BatteryCommunicationAdapter.charge_battery(self.ip, charge)

    def discharge_battery(self, charge):
        BatteryCommunicationAdapter.charge_battery(self.ip, -charge)

    def update_values(self):
        charge_state = self.get_charge_state()
        charge_rate = self.get_battery_charging_rate()
        response = {
            "battery":
                {
                    "stored_energy": charge_state,
                    "charging_rate": charge_rate
                }
        }
        if response != None:
            try:
                for value in self.values:
                    path = response

                    config_tags = value['tag'].split('.')
                    for config_tag in config_tags:
                        path = path[config_tag]

                    if ("multiplier" in value):
                        path *= value["multiplier"]
                    value['values'] = round(path, 4)
            except KeyError:
                utils.print_error("Key Error in " + self.name + " with tag " + config_tag)
            except TypeError:
                utils.print_error("Type Error in " + self.name)
        else:
            utils.print_error("ERROR! IN UPDATING VALUES OF IOT " + self.name)

    def run(self):
        while True:
            sleep(self.monitoring_period - time() % 1)
            self.update_values()
