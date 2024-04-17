import logging

from pyModbusTCP.client import ModbusClient
from pyModbusTCP.utils import get_2comp

logger = logging.getLogger(__name__)


def charge_battery(host: str, watts: int):
    """Charges and discharges the battery depending on the watts signal.

    Positive _watts_ charges the battery. Negative _watts_ discharges the battery.

    Args:
        host (str): Hostname or ip of the battery.
        watts (int): Value to be charged in watts.
    """
    client = ModbusClient(host=host, unit_id=100, auto_close=True)
    result = client.write_single_register(2700, get_2comp(watts))
    if result:
        logger.info(f'SUCCESS: changed battery charge to {watts} W.')
    else:
        logger.warn(f'FAIL: could not change battery charge. (host:{host};register:{2700};unit_id:{100};value:{watts})')


def get_battery_charging_rate(host: str) -> int:
    """Get battery charging rate.

    Args:
        host (str): Hostname or IP of the battery.

    Returns:
        int: Charging rate of the battery in Watts.
    """
    client = ModbusClient(host=host, unit_id=100, auto_close=True)
    result = client.read_input_registers(reg_addr=842)
    if result is not None:
        result = get_2comp(result[0])
        logger.info(f'SUCCESS: battery charging at {result} W.')
    else:
        logger.warn(f'FAIL: could not read battery charge. (host:{host};register:{842};unit_id:{100})')
    return result


def get_battery_state_of_charge(host: str) -> int:
    """Get state of charge of the battery.

    Args:
        host (str): Hostname or IP of the battery.

    Returns:
        int: State of charge of the battery in percentage.
    """
    client = ModbusClient(host=host, unit_id=100, auto_close=True)
    result = client.read_input_registers(reg_addr=843)
    if result is not None:
        result = get_2comp(result[0])
        logger.info(f'SUCCESS: battery state of charge is {result}%.')
    else:
        logger.warn(f'FAIL: could not read battery state of charge. (host:{host};register:{843};unit_id:{100})')
    return result
