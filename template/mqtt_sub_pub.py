from time import sleep
from umqtt.simple import MQTTClient
from machine import Pin
from dht import DHT22
import ubinascii
import machine
import micropython
import network, utime

#-----------Connect to WiFi
station = network.WLAN(network.STA_IF)
station.active(True)
station.connect("******", "******")
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
led = Pin(13, Pin.OUT, value=1) # led on GPIO 13
sensor = DHT22(Pin(15, Pin.IN, Pin.PULL_UP))   # DHT-22 on GPIO 15 (input with internal pull-up resistor)

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

broker_address = '*******'
client_id ='test1'
topic=b'led'
TOPIC2 = b'temp_humidity'
state=0

client = MQTTClient(client_id, broker_address, port=1883, user=b"*****", password=b"******")
client.set_callback(callback)
client.connect()
client.subscribe(b"led")

while True:
    if True:
        # Blocking wait for message
        client.wait_msg()
    else:
        # Non-blocking wait for message
        client.check_msg()
        # Then need to sleep to avoid 100% CPU usage (in a real
        # app other useful actions would be performed instead)
        time.sleep(1)
    try:
        sensor.measure()   # Poll sensor
        t = sensor.temperature()
        h = sensor.humidity()
        if isinstance(t, float) and isinstance(h, float):  # Confirm sensor results are numeric
            msg = (b'{0:3.1f},{1:3.1f}'.format(t, h))
            client.publish(TOPIC2, msg)  # Publish sensor data to MQTT topic
            print("Published", msg)

        else:
            print('Invalid sensor readings.')
    except OSError:
        print('Failed to read sensor.')
    sleep(4)
    client.disconnect()
