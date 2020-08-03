from machine import Pin
import machine
from time import sleep
from machine import Pin, I2C
import ssd1306
from network import WLAN
import urequests


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

def cvrk(sec = 2, d=1000, freq = 500):
    pin = machine.PWM(Pin(14), freq)
    pin.duty(d)
    sleep(sec)
    pin.duty(0)

i2c = I2C(-1, scl=Pin(22), sda=Pin(21))
oled_width = 128
oled_height = 64
oled = ssd1306.SSD1306_I2C(oled_width, oled_height, i2c)

oled.text("Zapnuty", 0, 0)
oled.show()
sleep(1)

# wlan = WLAN()
# wlan.active(True)
# if wlan.active():
#     wlan.connect("TreeCat", "vsade_dobre_doma_NAY")
#     while not wlan.isconnected():
#         machine.idle()  # save power while waiting
#     oled.text("Pripojeny", 0, 0)
#     oled.text(wlan.ifconfig()[0], 0, 8)
#     oled.show()
#     oled.text(http_get("http://pumec.zapto.org/"), 0, 16)
    # response = urequests.get('http://pumec.zapto.org/')
    # oled.text(response.text, 0, 16)
# else:
#     oled.text("Wifi nejde :(", 0, 0)
# oled.show()
#
# sleep(5)
# r = 0
# while True:
    # oled.text("Odmeral: " + str(zmeraj()), 0, r*8)
    # oled.show()
    # r = r + 1 if r < 4 else 0
    # if r==0:
    #     oled.fill(0)
# sleep(1)
zapni()
namerane = sum([zmeraj() for i in range(POCET_MERANI)]) / POCET_MERANI
vypni()
print("namerane: " + str(namerane))
if namerane > KONSTANTA:
    cvrk()
# machine.deepsleep(6 * 60 * 60 * 1000)
machine.deepsleep(10 * 1000)