from time import sleep
# microPython imports
from umqtt_simple import MQTTClient
from machine import Pin
from SHT30 import SHT30
import ubinascii
import machine
import micropython
import network, utime
import ujson

WIFI_SSID = '************'
WIFI_PW = '*********'

SERVER = '***********'
CLIENT_ID = '*********'
PORT = 1883
UN = '*********'
PW = '*********'
TOPIC = b'esp8266-2'
TOPIC_LED = b'led'
WAIT = 15   # wait time in seconds between measuring

#-----------Connect to WiFi
station = network.WLAN(network.STA_IF)
station.active(True)
station.connect(WIFI_SSID, WIFI_PW)
tmo = 50
while not station.isconnected():
    utime.sleep_ms(100)
    tmo -= 1
    if tmo == 0:
        break
if tmo > 0:
    ifcfg = station.ifconfig()
    print("WiFi started, IP:", ifcfg[0])
    utime.sleep_ms(500)
#-----------------
led = Pin(2, Pin.OUT, value=1) # led on GPIO 13
# sensor = DHT22(Pin(15, Pin.IN, Pin.PULL_UP))   # DHT-22 on GPIO 15 (input with internal pull-up resistor)
sensor = SHT30()
sensor.set_delta(0.0, 0.0)

def callback(topic, msg):
    global state
    print((topic, msg))
    if msg == b"on":
        led.value(1)
        state = 0
    elif msg == b"off":
        led.value(0)
        state = 1
    elif msg == b"toggle":
        # LED is inversed, so setting it to current state
        # value will make it toggle
        led.value(state)
        state = 1 - state

broker_address = SERVER
state=0

client = MQTTClient(CLIENT_ID, broker_address, port=1883, user=UN, password=PW)
client.set_callback(callback)

i = 0
while True:
    i += 1
    client.connect()
    client.subscribe(TOPIC_LED)
    client.check_msg()

    if i % WAIT == 0:
        try:
            t, h = sensor.measure()   # measure temperature and humidity values
            if isinstance(t, float) and isinstance(h, float):  # Confirm sensor values are numeric
                data['Temperature'] = t
                data['Humidity'] = h
                data['Time'] = time.time()
                msg = ujson.dumps(data).encode()
                client.publish(TOPIC, msg)  # Publish sensor readings to MQTT topic
                print(msg)
            else:
                print('Invalid sensor readings.')
        except OSError:
            print('Failed to read sensor.')
    client.disconnect()
    sleep(1)

