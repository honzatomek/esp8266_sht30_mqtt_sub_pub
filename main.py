#embedded modules
print('\n[i] importing embedded modules')
import machine
from utime import sleep_ms, time
import ntptime
from ujson import dumps, loads
from umqtt.simple import MQTTClient

# personal modules
print('[i] importing personal modules')
from config import *
from SHT30 import SHT30
from wifi import WiFi


# global variables
print('[i] assigning global variables')
led = machine.Pin(2, machine.Pin.OUT, value=1)
sensor = SHT30()
wifi = WiFi(WIFI_SSID, WIFI_PW)
rtc = machine.RTC()
rtc.irq(trigger=rtc.ALARM0, wake=machine.DEEPSLEEP)


# help functions
def blink(number=3, duration=250):
    print('[i] running function: blink()')
    global led
    for i in range(2 * number):
        led.value(not led.value())
        sleep_ms(duration)


def connect():
    print('[i] running function: connect()')
    global wifi
    global rtc
    if not wifi.isconnected():
        connected = False
        while not connected:
            try:
                connected = wifi.connect()
            except Exception:
                rtc.alarm(rtc.ALARM0, 1000 * 30)
                machine.deepsleep()
    print('[i] wifi connected.')
    blink(3)


connect()
print('[i] setting correct time')
ntptime.settime()  # set the rtc datetime from the remote server


def callback(topic, msg):
    print('[i] running function callback() for topic: {0}'.format(topic))
    try:
        message = loads(msg)
        print(message)
        for key in message:
            if key == 'led':
                global led
                if message[key] == 'on':
                    led.value(0)
                elif message[key] == 'off':
                    led.value(1)
                else:
                    led.value(not led.value())
            elif key == 'temp':
                global sensor
                t, h = sensor.measure()
                if isinstance(t, float) and isinstance(h, float):
                    print('[i] setting delta_temp value to: {0}.'.format(float(message[key]) - t + sensor.delta_temp))
                    sensor.set_delta(delta_temp=float(message[key]) - t + sensor.delta_temp)
            elif key == 'humidity':
                global sensor
                t, h = sensor.measure()
                if isinstance(t, float) and isinstance(h, float):
                    print('[i] setting delta_hum value to: {0}.'.format(float(message[key]) - h + sensor.delta_hum))
                    sensor.set_delta(delta_hum=float(message[key]) - h + sensor.delta_hum)
            else:
                blink(1)
    except Exception as e:
        print('[-] Payload is not in json format.')
        print('    payload: {0}'.format(msg))


print('[i] setting up mqtt client')
mqtt = MQTTClient(MQTT_CLIENT_ID, MQTT_BROKER)
mqtt.set_callback(callback)
mqtt.connect()
mqtt.subscribe(TOPIC_IN)


def measure_and_publish():
    print('[i] running function measure_and_publish()')
    global sensor
    global mqtt
    global rtc
    global led
    data = dict()
    tm = rtc.datetime()     # get the date and time in UTC
    t, h = sensor.measure()
    l = 'on' if led.value() == 0 else 'off'
    if isinstance(t, float) and isinstance(h, float):
        data['temperature'] = {'value': t, 'units': 'C'}
        data['humidity'] = {'value': h, 'units': '%'}
        data['time'] = {'date': '{0:04}/{1:02}/{2:02}'.format(tm[0], tm[1], tm[2]),
                        'time': '{0:02}:{1:02}:{2:02}.{3:03}'.format(tm[4], tm[5], tm[6], tm[7])}
        data['led'] = l
        mqtt.publish(TOPIC_OUT, dumps(data))


measure_and_publish()
i = 0
print('[i] running main loop')
while True:
    try:
        i += SUBSCRIBE_DELAY
        mqtt.check_msg()
        if i >= PUBLISH_DELAY:
            measure_and_publish()
            i = 0
        sleep_ms(SUBSCRIBE_DELAY)
    except Exception as e:
        print(e)
        machine.reset()
