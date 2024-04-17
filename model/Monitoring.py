import sys
from datetime import datetime
from threading import Thread
from time import time, sleep

sys.path.append(".")


class Monitoring(Thread):
    def __init__(self, core):
        Thread.__init__(self)
        self.core = core

    # Stop Monitoring
    def stop_monitoring(self):
        sys.exit()

    def run(self):
        # schedule.every().day.at("22:00").do(self.run_thread_schedule, forecastday)
        sleep(5 - time() % 1)
        while True:
            sleep(1 - time() % 1)
            # print(datetime.now())
            # print("Total consumption: " + str(self.core.get_total_consumption()))
            # print("Total current: " + str(self.core.get_total_current()))
            # print()
