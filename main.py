import machine
from machine import Pin, I2C
# import ssd1306
from network import WLAN
import uasyncio as asyncio
import config
import uaiohttpclient

PIN_SENZOR_2_0 = 33
PIN_SENZOR_STRED_1_2 = 32
PIN_SENZOR_KRAJ_1_2 = 35
PIN_NAPAJANIE_SENZOR = 27


KONSTANTA = 2000
SEKUND_SUCHA = 60 * 60 * 24 * 2
MERANIE_POCET = 5
MERANIE_PAUZA = 1

def setupRTC():
    import ntptime
    ntptime.settime()

def setupWDT():
     machine.WDT(timeout=60000)


async def zmeraj():
    napajanie_senzor = machine.Pin(PIN_NAPAJANIE_SENZOR, machine.Pin.OUT)
    napajanie_senzor.value(True)
    vstup = machine.ADC(Pin(PIN_SENZOR_2_0))
    hodnoty = []
    for i in range(MERANIE_POCET):
        await asyncio.sleep(MERANIE_PAUZA)
        hodnoty.append(vstup.read())
    napajanie_senzor.value(False)
    data = round(sum(hodnoty) / len(hodnoty))
    print(str(data))
    return data

async def zmeraj(pinSensor, text):
    napajanie_senzor = machine.Pin(PIN_NAPAJANIE_SENZOR, machine.Pin.OUT)
    napajanie_senzor.value(True)
    vstup = machine.ADC(Pin(pinSensor))
    hodnoty = []
    for i in range(MERANIE_POCET):
        await asyncio.sleep(MERANIE_PAUZA)
        hodnoty.append(vstup.read())
    napajanie_senzor.value(False)
    data = round(sum(hodnoty) / len(hodnoty))
    print(str(text) + ": "+str(data))
    return data

async def stop():
    loop = asyncio.get_event_loop()
    print("stop")
    loop.stop()


async def cvrk(sec=2, d=1000, freq=500):
    pin = machine.PWM(Pin(14), freq)
    pin.duty(d)
    await asyncio.sleep(sec)
    pin.duty(0)


# def nachystaj_displej():
#     i2c = I2C(-1, scl=Pin(22), sda=Pin(21))
#     oled_width = 128
#     oled_height = 64
#     return ssd1306.SSD1306_I2C(oled_width, oled_height, i2c)
#
#
# oled = nachystaj_displej()
# oled.text("Zapnuty", 0, 0)
# oled.show()

wlan = WLAN()
wlan.active(True)
if wlan.active():
    wlan.connect(config.WIFI_SSID, config.WIFI_PAS)
    while not wlan.isconnected():
        machine.idle()  # save power while waiting
    # oled.text("Pripojeny", 0, 0)
    # oled.text(wlan.ifconfig()[0], 0, 8)
    # oled.show()
    # response = urequests.get('http://pumec.zapto.org/')
    # oled.text(response.text, 0, 16)

setupWDT()
setupRTC()

async def ohlassa():
    await uaiohttpclient.run(method="POST", url="http://" + config.TB_URL + ":8080/api/v1/" + config.TB_DEVICE_ID_1 + "/telemetry", data="{\"iny_nazov_kluca\": 54}")

async def senddata(pinSensor, text, deviceKey):
    data = await zmeraj(pinSensor, text)
    await uaiohttpclient.run(method="POST", url="http://" + config.TB_URL + ":8080/api/v1/" + deviceKey + "/telemetry", data="{\"tmp\": "+str(data)+"}")
#
# import upip
# upip.install('micropython-uasyncio')

# loop = asyncio.get_event_loop()
# loop.run_forever()
for x in range(6):
    loop = asyncio.get_event_loop()
    loop.call_soon(senddata(PIN_SENZOR_2_0, 2.0, config.TB_DEVICE_ID_1))
    loop.call_soon(senddata(PIN_SENZOR_STRED_1_2, "1.2-stred", config.TB_DEVICE_ID_2))
    loop.call_soon(senddata(PIN_SENZOR_KRAJ_1_2, "1.2-kraj", config.TB_DEVICE_ID_3))
    loop.call_later(15, stop())
    print("iteracia")
    loop.run_forever()

    # tasks = loop.create_task(zmeraj(PIN_SENZOR_2_0, 2.0))
    # tasks = loop.create_task(zmeraj(PIN_SENZOR_2_0, 2.0))
    # tasks = loop.create_task(zmeraj(PIN_SENZOR_2_0, 2.0))

    # loop.create_task(stop())
    # print("mam tasks")
    # loop.run_forever()




    # loop.run_until_complete(zmeraj(PIN_SENZOR_2_0, 2.0))
    # loop.close()



# if namerane > KONSTANTA:
#     cvrk()
# machine.deepsleep(6 * 60 * 60 * 1000)
# machine.deepsleep(10 * 1000)
