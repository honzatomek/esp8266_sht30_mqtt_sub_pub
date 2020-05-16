import network
from utime import sleep_ms

class WiFi:
    def __init__(self, ssid, password):
        self.__ssid = ssid
        self.__password = password
        self.__ap_if = network.WLAN(network.AP_IF)
        self.__sta_if = network.WLAN(network.STA_IF)

    def connect(self, timeout_ms=5000):
        self.__ap_if.active(False)
        self.__sta_if.active(True)
        print('[+] Connecting to network "{0}'.format(self.__ssid))
        self.__sta_if.connect(self.__ssid, self.__password)
        delay = 100
        for i in range(int(timeout_ms / delay)):
            sleep_ms(delay)
            if self.__sta_if.isconnected():
                return '[+] Connected to {0} as {1}'.format(self.__ssid, self.__sta_if.ifconfig()[0])
        raise Exception('[-] Problem connecting to {0}.'.format(self.__ssid))

    def disconnect(self):
        self.__sta_if.disconnect()

    def isconnected(self):
        return self.__sta_if.isconnected()

    def ifconfig(self):
        return self.__sta_if.ifconfig()
