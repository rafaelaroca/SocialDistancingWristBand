# COVID19 Social Distancing Bracelet using MicroPyhton and ESP32

import bluetooth
import random
import struct
import time
import urandom
import machine
from ble_advertising import advertising_payload

from ble_advertising import decode_services, decode_name

from micropython import const
import ubinascii

_IRQ_CENTRAL_CONNECT = const(1)
_IRQ_CENTRAL_DISCONNECT = const(2)
_IRQ_SCAN_RESULT = const(5)
_IRQ_SCAN_DONE = const(6)

_ADV_IND = const(0x00)
_ADV_DIRECT_IND = const(0x01)
_ADV_SCAN_IND = const(0x02)
_ADV_NONCONN_IND = const(0x03)

_ENV_SENSE_UUID = bluetooth.UUID(0x181A)

_TEMP_CHAR = (
    bluetooth.UUID(0x2A6E),
    bluetooth.FLAG_READ | bluetooth.FLAG_NOTIFY,
)
_ENV_SENSE_SERVICE = (
    _ENV_SENSE_UUID,
    (_TEMP_CHAR,),
)

_ADV_APPEARANCE_GENERIC_THERMOMETER = const(768)

class BLESocialDistance:
    def __init__(self, ble, name="covid19"):
        self._ble = ble
        self._ble.active(True)
        self._ble.irq(handler=self._irq)
        ((self._handle,),) = self._ble.gatts_register_services((_ENV_SENSE_SERVICE,))
        self._connections = set()
#        name = "covid" + ubinascii.hexlify(b'~\xd8\xc6\x00').decode('utf-8')
        name = "covid" + str(urandom.getrandbits(30))
        self.name=name
        self._payload = advertising_payload(
            name=name, services=[_ENV_SENSE_UUID], appearance=_ADV_APPEARANCE_GENERIC_THERMOMETER
        )
        self._advertise()

    def _irq(self, event, data):

        if event == _IRQ_CENTRAL_CONNECT:
            conn_handle, _, _, = data
            self._connections.add(conn_handle)
        elif event == _IRQ_CENTRAL_DISCONNECT:
            conn_handle, _, _, = data
            self._connections.remove(conn_handle)

            self._advertise()

        if event == _IRQ_SCAN_RESULT:
            addr_type, addr, adv_type, rssi, adv_data = data
            if adv_type in (_ADV_IND, _ADV_DIRECT_IND,) and _ENV_SENSE_UUID in decode_services(
                adv_data
            ):

                self._addr_type = addr_type
                self._addr = bytes(
                    addr
                )  # Note: addr buffer is owned by caller so need to copy it.

                k = decode_name(adv_data) or "?"
                print ("Found: " + k + " RSSI = " + str(rssi))
                print ("I am: " + self.name + " RSSI = " + str(rssi))
                x = rssi*-1
                if x > 60:
                    print("LED ON")
                    p = machine.Pin(2, machine.Pin.OUT)
                    p.on()
                else:
                    print("LED OFF")
                    p = machine.Pin(2, machine.Pin.OUT)
                    p.off()
                self._ble.gap_scan(None)
                print ("stopped. Scanning again")
                self._ble.gap_scan(2000, 30000, 30000)

    def _advertise(self, interval_us=500000):
        self._ble.gap_advertise(interval_us, adv_data=self._payload)


def demo():
    ble = bluetooth.BLE()
    temp = BLESocialDistance(ble)

    print("Start")
    while True:
        print("Scanning")
        ble.gap_scan(2000, 30000, 30000)
        print("End Scanning")
        time.sleep_ms(1000)


if __name__ == "__main__":
    demo()



