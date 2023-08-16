import network
import hashlib
import ntptime
from machine import RTC, Timer
import wifimgr
import time
import urequests
import tft_config
import st7789
import romans as script_font
import display_helpers as dh

NTP_TO_GMT = 946684800  # needed to convert ntptime.time() to normal UNIX timestamp

INIT_URL = "https://app.thequietworkplace.com/api/external/init"
DISPLAY_URL = "https://app.thequietworkplace.com/api/external/room/display"

NTP_UPDATE_PERIOD = 3600 * 1000 * 6  # milliseconds in an hour * hours
RES_UPDATE_PERIOD = 1000 * 15  # milliseconds in 15 seconds

RESERVATION_CHECK_MINUTES = (9, 24, 39, 54, 37, 38, 39)
RESERVATION_CHECK_LOCKOUT = 60000

QW_BLUE = st7789.color565(48, 89, 151)
BLACK = st7789.BLACK
WHITE = st7789.WHITE
RED = st7789.RED

wlan = network.WLAN(network.STA_IF)
rtc = RTC()

tft = tft_config.config(1)

tft.init()
tft.offset(1, 35)  # offset for config 1

tft.fill(st7789.color565(48, 89, 151))


def update_ntptime():
    try:
        ntptime.settime()
        return None
    except OSError as e:
        print(f"Time update error: {e}")  # add to display


def build_init_headers():
    device_id = wlan.config('mac').hex()
    pin = hashlib.sha1(device_id).digest().hex()
    device_type = "unit_display"
    return {"device-id": device_id, "pin": pin, "device-type": device_type}


def print_resp_info(resp):
    print(f"Status code: {resp.status_code}")
    print(f"Resp text: {resp.text}")
    dh.draw_multiline_text(tft, script_font, (f"Status code: {resp.status_code}", f"Resp text: {resp.text}"))
    time.sleep(2)


def build_display_headers():
    device_id = wlan.config('mac').hex()
    pin = hashlib.sha1(device_id).digest().hex()
    return {"device-id": device_id, "pin": pin}


def callback_ntp_update(t):
    ntptime.settime()


def current_epoch():
    return ntptime.time() + NTP_TO_GMT


# Config wifi
wlan_sta = wifimgr.get_connection()

if wlan_sta is not None:
    while not wlan_sta.isconnected():
        dh.draw_multiline_text(tft, script_font, ("Connecting to:", f"{wlan_sta.config('ssid')}"))

    dh.draw_multiline_text(tft, script_font, ("Connected to:", f"{wlan_sta.config('ssid')}"))
else:
    print("Unable to connect to wifi")
    print("Please check wifi credentials")
    dh.draw_multiline_text(tft, script_font, ("No wifi", "Check credentials"))

time.sleep(2)

# Update time
if rtc.datetime()[0] < 2023:
    for _ in range(3):
        update_ntptime()
        if rtc.datetime()[0] >= 2023:
            break
        time.sleep(1)
print(rtc.datetime())

tm = rtc.datetime()
dh.draw_multiline_text(tft, script_font, (f"Date: {tm[1]}/{tm[2]}/{tm[0]}", f"Time: {tm[4]}:{tm[5]}:{tm[6]}"))
time.sleep(3)

# Register with server
init_headers = build_init_headers()

init_resp = urequests.get(INIT_URL, headers=init_headers)

if init_resp.status_code == 200:
    payload = init_resp.json()  # {"room_id":"5552f269-e0c3-4a39-8f40-4f7a3ead3887","display":"Q1","offset":240}
    room_id = payload["room_id"]
    unit_name = payload["display"]
    time_offset = payload["offset"]

    dh.draw_multiline_text(tft, script_font, (f"Unit name: {unit_name}",))
    time.sleep(15)
    tft.fill(BLACK)
else:
    while True:
        reg_resp = urequests.get(INIT_URL, headers=init_headers)

        print(reg_resp.status_code)

        if reg_resp.status_code == 201 or init_resp.status_code == 401:
            # init registration successful / pending allocation
            print("Registered. Please assign to unit in admin portal.")
            dh.draw_multiline_text(tft, script_font, ("Registered as:", f"{wlan.config('mac').hex()}"))
        elif reg_resp.status_code == 200:
            break
        else:
            print("Please contact manufacturer.")
            dh.draw_multiline_text(tft, script_font, ("Please contact:", "manufacturer"))

        time.sleep(60)

tft.deinit()

timer_ntp = Timer(0)
timer_ntp.init(mode=Timer.PERIODIC, period=NTP_UPDATE_PERIOD, callback=callback_ntp_update)

display_headers = build_display_headers()
last_check = 0

res_end = -1  # set to
active_reservation = False

while True:
    _, _, _, _, hr, mins, _, _ = rtc.datetime()  # (year, month, day, weekday, hours, minutes, seconds, subseconds)
    # check for an active reservation
    if mins in RESERVATION_CHECK_MINUTES and time.ticks_diff(time.ticks_ms(), last_check) > RESERVATION_CHECK_LOCKOUT:
        display_resp = urequests.get(DISPLAY_URL, headers=display_headers)
        if display_resp.status_code == 200:
            last_check = time.ticks_ms()
            print(f"Periodic check result: {display_resp.text}")
            res_end = display_resp.json()["end"]
            if res_end >= 0:  # -1 is value if no reservation exists
                active_reservation = True
        else:
            print("Error connecting to server")  # Update display if it errors out?
            time.sleep_ms(500)  # don't constantly try to ping the server

    # reservation end {'end': 1691772300} - this payload was for GMT checkout time

    # TODO: Add checking within loop to break out if reservation is extended (not needed now)
    if active_reservation and res_end - current_epoch() < 330:  # verify units and math associated with this 5.5 minutes
        tft.init()

        # TODO: Update display for 5 minutes remaining
        while True:
            time_left = res_end - current_epoch()  # in seconds
            if time_left <= 0 and active_reservation:
                print("Please leave the space.")
                print("Draw red screen.")
                dh.draw_multiline_text(tft, script_font, ("Please", "Checkout"), fill=RED)
                display_resp = urequests.get(DISPLAY_URL, headers=display_headers)
                if display_resp.status_code == 200:
                    if display_resp.json()["end"] == -1:
                        active_reservation = False
                        break
                    else:
                        res_end = display_resp.json()["end"]
                time.sleep(30)  # prevents constant ping of server when not checked out
            elif 50 < (time_left % 60) < 60:
                print(f"Draw display with {time_left // 60} bars")
                dh.draw_bars(tft, time_left // 60)
                display_resp = urequests.get(DISPLAY_URL, headers=display_headers)
                if display_resp.status_code == 200:
                    if display_resp.json()["end"] == -1:
                        active_reservation = False
                        break
                    else:
                        res_end = display_resp.json()["end"]
                time.sleep(10)  # prevents multiple calls to server at rollover of minute
            elif 28 < (time_left % 60) < 32 or 13 < (time_left % 60) < 17:
                display_resp = urequests.get(DISPLAY_URL, headers=display_headers)
                if display_resp.status_code == 200:
                    if display_resp.json()["end"] == -1:
                        active_reservation = False
                        break
                    else:
                        res_end = display_resp.json()["end"]
        tft.deinit()
