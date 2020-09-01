import machine
from machine import Pin#, I2C
# import ssd1306
from network import WLAN
import uasyncio as asyncio
import uaiohttpclient as aiohttp

PIN_SENZOR = 33
PIN_NAPAJANIE_SENZOR = 27

KONSTANTA = 2000
SEKUND_SUCHA = 60 * 60 * 24 * 2
MERANIE_POCET = 5
MERANIE_PAUZA = 1


async def zmeraj():
    napajanie_senzor = machine.Pin(PIN_NAPAJANIE_SENZOR, machine.Pin.OUT)
    napajanie_senzor.value(True)
    vstup = machine.ADC(Pin(PIN_SENZOR))
    hodnoty = []
    for i in range(MERANIE_POCET):
        await asyncio.sleep(MERANIE_PAUZA)
        hodnoty.append(vstup.read())
    napajanie_senzor.value(False)
    return round(sum(hodnoty) / len(hodnoty))


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
    wlan.connect("SSID", "heslo")
    while not wlan.isconnected():
        machine.idle()  # save power while waiting
    # oled.text("Pripojeny", 0, 0)
    # oled.text(wlan.ifconfig()[0], 0, 8)
    # oled.show()
    # response = urequests.get('http://pumec.zapto.org/')
    # oled.text(response.text, 0, 16)


async def run(method, url, data=None):
    resp, writer = await aiohttp.request(method=method, url=url, data=data, timeout=30)
    text = await resp.read()
    writer.aclose()
    text = text.decode("ascii")
    resp.text = text
    return resp

async def getDateTime():
    response = await run(method="POST", url="http://192.168.1.26:8080/api/v1/1oC2DlvMktSdNZLnmhKZ/telemetry", data="{\"iny_nazov_kluca\": 54}")
    datestring = response.headers["Date"]
    print("Mam datum: " + datestring)
    # date = datetime.strptime(datestring, " %a, %d %b %Y %H:%M:%S %Z")
    # print("naparsovane")
    # print(str(date.hour))
    return datestring

async def ohlassa():
    datum = await getDateTime()

asyncio.set_debug(True)
loop = asyncio.get_event_loop()
loop.run_until_complete(ohlassa())
loop.close()

# if namerane > KONSTANTA:
#     cvrk()
# machine.deepsleep(6 * 60 * 60 * 1000)
# machine.deepsleep(10 * 1000)
