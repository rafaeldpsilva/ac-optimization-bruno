import sys
from datetime import datetime, timedelta
from threading import Thread
from time import time, sleep
import schedule

sys.path.append(".")
from services.BuildingService import BuildingService
from database.BuildingRepository import BuildingRepository
from database.IotRepository import IotRepository
from database.BatteryRepository import BatteryRepository


class StoringManager(Thread):
    def __init__(self, core, storing_frequency, hour_offset):
        Thread.__init__(self)
        self.core = core
        self.storing_frequency = storing_frequency
        self.hour_offset = hour_offset

    def stop_saving(self):
        sys.exit()

    def save_batteries_values(self):
        battery_repo = BatteryRepository()
        batteries = []
        for i in self.core.batteries:
            batteries.append({"name": i.name, "values": i.values})
        battery_repo.insert_batteries(batteries)

    def save_iot_values(self):
        iot_repo = IotRepository()
        iots = []
        for i in self.core.iots:
            iots.append({"name": i.name, "type": i.type, "values": i.values})
        iot_repo.insert_iots(iots, datetime.now() + timedelta(hours=self.hour_offset))

    def save_total(self):
        building_repo = BuildingRepository()
        building_repo.insert_total(self.core.get_total_consumption(), self.core.get_total_generation(),
                                   datetime.now() + timedelta(hours=self.hour_offset))

    def save_hour(self):
        building_service = BuildingService()
        building_service.save_last_hour()

    def run(self):
        schedule.every().hour.at(":00").do(self.save_hour)
        while True:
            sleep(self.storing_frequency - time() % 1)
            self.save_iot_values()
            self.save_batteries_values()
            self.save_total()
            schedule.run_pending()
