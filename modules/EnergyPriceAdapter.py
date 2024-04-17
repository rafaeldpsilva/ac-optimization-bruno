from utils import utils


def get_price_now():
    response = utils.update_values_get("energy price", "192.168.2.68:5000/now")
    return response['price']


def get_price_next():
    response = utils.update_values_get("energy price", "192.168.2.68:5000/next")
    return response['price']


def get_price_today():
    response = utils.update_values_get("energy price", "192.168.2.68:5000/today")
    return response['price']


def get_price_tomorrow():
    response = utils.update_values_get("energy price", "192.168.2.68:5000/tomorrow")
    return response['price']


def get_price_all():
    response = utils.update_values_get("energy price", "192.168.2.68:5000/all")
    return response['price']
