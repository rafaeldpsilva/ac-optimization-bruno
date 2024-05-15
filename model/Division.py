import pandas as pd

from modules import ACStatusAdapter

class Division:
    def __init__(self, name, iots, id="", ac_status_configuration=""):
        self.name = name
        self.iots = iots
        self.id = id
        self.ac_status_configuration = ac_status_configuration