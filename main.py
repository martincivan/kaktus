from machine import Pin
import machine
from time import sleep
from machine import Pin, I2C
import ssd1306
from network import WLAN
import uasyncio as asyncio
import uaiohttpclient as aiohttp

KONSTANTA = 2000
POCET_MERANI = 5

napajanie_senzor = machine.Pin(27, machine.Pin.OUT)
vstup = machine.ADC(Pin(33))


def zapni():
    napajanie_senzor.value(True)


def zmeraj():
    sleep(1)
    return vstup.read()


def vypni():
    napajanie_senzor.value(False)


def cvrk(sec=2, d=1000, freq=500):
    pin = machine.PWM(Pin(14), freq)
    pin.duty(d)
    sleep(sec)
    pin.duty(0)


def nachystaj_displej():
    i2c = I2C(-1, scl=Pin(22), sda=Pin(21))
    oled_width = 128
    oled_height = 64
    return ssd1306.SSD1306_I2C(oled_width, oled_height, i2c)


oled = nachystaj_displej()
oled.text("Zapnuty", 0, 0)
oled.show()

wlan = WLAN()
wlan.active(True)
if wlan.active():
    wlan.connect("SSID", "heslo")
    while not wlan.isconnected():
        machine.idle()  # save power while waiting
    oled.text("Pripojeny", 0, 0)
    oled.text(wlan.ifconfig()[0], 0, 8)
    oled.show()
    # response = urequests.get('http://pumec.zapto.org/')
    # oled.text(response.text, 0, 16)
# else:
#     oled.text("Wifi nejde :(", 0, 0)
# oled.show()

def nainstaluj():
    import upip
    upip.install('micropython-uasyncio')
    upip.install('micropython-uasyncio.synchro')
    upip.install('micropython-uasyncio.queues')

    oled.text("Stiahnute", 0, 8)
    oled.show()


def print_stream(resp):
    print((yield from resp.read()))
    return
    while True:
        line = yield from reader.readline()
        if not line:
            break
        print(line.rstrip())


def run(url):
    resp = yield from aiohttp.request("POST", url, data="{\"iny_nazov_kluca\": 54}", timeout=30)
    print(resp)
    yield from print_stream(resp)


loop = asyncio.get_event_loop()
loop.run_until_complete(run("http://pumec.zapto.org:8080/api/v1/9Pt11blnxGVHNHETiop9/telemetry"))
loop.close()
#
sleep(5)
r = 0
while True:
    oled.text("Odmeral: " + str(zmeraj()), 0, r*8)
    oled.show()
    r = r + 1 if r < 4 else 0
    if r==0:
        oled.fill(0)
sleep(1)
zapni()
namerane = sum([zmeraj() for i in range(POCET_MERANI)]) / POCET_MERANI
vypni()
print("namerane: " + str(namerane))
if namerane > KONSTANTA:
    cvrk()
# machine.deepsleep(6 * 60 * 60 * 1000)
machine.deepsleep(10 * 1000)
