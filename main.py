# standard imports
import time
from time import sleep

# microPython imports
import machine
from machine import Timer, Pin
import network
import ujson
from SHT30 import SHT30
from umqtt_simple import MQTTClient


WIFI_SSID = '************'
WIFI_PW = '*********'

SERVER = '***********'
CLIENT_ID = '*********'
PORT = 1883
UN = '*********'
PW = '*********'
TOPIC = b'esp8266-2'
# TOPIC_LED = b'esp8266-2/led'
TOPIC_LED = b'led'
WAIT = 15   # wait time in seconds between measuring

STATE = 1
LED = Pin(2, Pin.OUT, STATE)

def timeout_callback(t):
    raise Exception('WiFi connection timeout!')


def do_connect():
    network.WLAN(network.AP_IF).active(False)
    sta_if = network.WLAN(network.STA_IF)
    if not sta_if.isconnected():
        print('connecting to network "{0}"'.format(WIFI_SSID))
        sta_if.active(True)
        sta_if.connect(WIFI_SSID, WIFI_PW)
        while not sta_if.isconnected():
            pass
    print('network config:', sta_if.ifconfig())

    if sta_if.ifconfig()[0] != '0.0.0.0':
        print('connected')
        p = Pin(2, Pin.OUT, 1)
        for i in range(6):
            p.value(not p.value())
            sleep(0.3)
        p.value(1)


def check_connection():
    sta_if = network.WLAN(network.STA_IF)
    return sta_if.isconnected()


def connect():
    timer = Timer(0)
    TIMEOUT_MS = 5000
    timer.init(period=TIMEOUT_MS, mode=Timer.ONE_SHOT, callback=timeout_callback)
    try:
        do_connect()
        timer.deinit()
    except:
        print('Connection timeout!')


def callback_led(topic, msg):
    # global state
    print((topic, msg))
    if msg == b"on":
        LED.value(1)
        STATE = 0
    elif msg == b"off":
        LED.value(0)
        STATE = 1
    elif msg == b"toggle":
        # LED is inversed, so setting it to current state
        # value will make it toggle
        LED.value(STATE)
        STATE = 1 - STATE


def check():
    c = MQTTClient(CLIENT_ID, SERVER, port=PORT, user=UN, password=PW)     # (client, server, port, user, password)
    c.set_callback(callback_led)
    c.connect()
    c.subscribe(TOPIC_LED)
    c.check_msg()
    sleep(1)
    c.disconnect()


def measure():
    c = MQTTClient(CLIENT_ID, SERVER, port=PORT, user=UN, password=PW)     # (client, server, port, user, password)
    c.connect()
    #c.publish(b'foo_topic', b'{0} - hello'.format(time.time()))
    sensor = SHT30()
    sensor.set_delta(0.0, 0.0)
    data = {}
#   t, h = sensor.measure()
    try:
        t, h = sensor.measure()   # measure temperature and humidity values
        if isinstance(t, float) and isinstance(h, float):  # Confirm sensor values are numeric
            data['Temperature'] = t
            data['Humidity'] = h
            data['Time'] = time.time()
            msg = ujson.dumps(data).encode()
            # msg = (b'Time: {0}, Temperature: {1:3.2f}, Humidity: {2:3.2f}'.format(time.time(), t, h))
            c.publish(TOPIC, msg)  # Publish sensor readings to MQTT topic
            print(msg)
        else:
            print('Invalid sensor readings.')
    except OSError:
        print('Failed to read sensor.')
    c.disconnect()


def main():
    try:
        i = 0
        while True:
            i += 1
            if not check_connection():
                connect()
            check()
            if ( i % (WAIT - 1) ) == 0:
                measure()
                i = 0
            # sleep(WAIT)
            sleep(1.0)
    except Exception:
        print('Connection timeout!')
        machine.reset()


if __name__ == '__main__':
    main()
