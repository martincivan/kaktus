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

PIN_TOUCH = 4


KONSTANTA = 2000
SEKUND_SUCHA = 60 * 60 * 24 * 2
MERANIE_POCET = 5
MERANIE_PAUZA = 1

def setupRTC():
    import ntptime
    ntptime.settime()

def setupWDT():
     machine.WDT(timeout=60000)


# async def zmeraj():
#     napajanie_senzor = machine.Pin(PIN_NAPAJANIE_SENZOR, machine.Pin.OUT)
#     napajanie_senzor.value(True)
#     vstup = machine.ADC(Pin(PIN_SENZOR_2_0))
#     hodnoty = []
#     for i in range(MERANIE_POCET):
#         await asyncio.sleep(MERANIE_PAUZA)
#         hodnoty.append(vstup.read())
#     napajanie_senzor.value(False)
#     data = round(sum(hodnoty) / len(hodnoty))
#     print(str(data))
#     return data

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
    if pinSensor is PIN_SENZOR_2_0 and data > 1250:
        await cvrk(6, 1000, 900)
    else:
        await ohlassa(config.TB_DEVICE_WATER_PUMP, 0)
    return data

async def ohlassa(deviceKey, data):
    print("odosielam polievam "+str(data))
    await uaiohttpclient.run(method="POST", url="http://" + config.TB_URL + ":8080/api/v1/" + deviceKey + "/telemetry", data="{\"iny_nazov_kluca\": "+str(data)+"}")

def instalUasyncio():
    import upip
    upip.install('micropython-uasyncio')

async def stop():
    loop = asyncio.get_event_loop()
    print("stop")
    loop.stop()

async def cvrk(sec=4, d=1000, freq=500):
    await ohlassa(config.TB_DEVICE_WATER_PUMP, 1000)
    pin = machine.PWM(Pin(14), freq)
    pin.duty(d)
    await asyncio.sleep(sec)
    pin.duty(0)

async def senddata(pinSensor, text, deviceKey):
    wdt = machine.WDT(timeout=60000)
    wdt.feed()
    data = await zmeraj(pinSensor, text)
    await uaiohttpclient.run(method="POST", url="http://" + config.TB_URL + ":8080/api/v1/" + deviceKey + "/telemetry", data="{\"tmp\": "+str(data)+"}")


wlan = WLAN()
wlan.active(True)
if wlan.active():
    wlan.connect(config.WIFI_SSID, config.WIFI_PAS)
    while not wlan.isconnected():
        machine.idle()
# save power while waiting
t = machine.TouchPad(Pin(PIN_TOUCH))
t.config(500)
read = t.read()
print(read)

if read < 200:
    led = Pin(2, Pin.OUT)
    led.value(True)
    # instalUasyncio()
    exit(0)

setupWDT()

setupRTC()


loop = asyncio.get_event_loop()
loop.call_soon(senddata(PIN_SENZOR_2_0, 2.0, config.TB_DEVICE_ID_1))
loop.call_later(15, stop())
print("iteracia")
loop.run_forever()

machine.deepsleep(10 * 1000)
