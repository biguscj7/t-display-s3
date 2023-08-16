import network
import mytime as ntptime
from machine import RTC, Timer
import wifimgr
import time
import tft_config
import st7789
import romans as script_font
import display_helpers as dh
import server_tools

NTP_TO_UNIX = 946684800  # needed to convert ntptime.time() to normal UNIX timestamp

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


def update_ntptime(t):
    try:
        ntptime.settime()
        print("Attempted ntp update")
    except OSError as e:
        print(f"Time update error: {e}")  # add to display


def current_epoch():
    return time.time() + NTP_TO_UNIX


# Config wifi
wlan_sta = wifimgr.get_connection()

if wlan_sta is not None:
    while not wlan_sta.isconnected():
        dh.draw_multiline_text(tft, script_font, ("Connecting to:", f"{wlan_sta.config('ssid')}"))

    dh.draw_multiline_text(tft, script_font, ("Connected to:", f"{wlan_sta.config('ssid')}"))
    time.sleep(2)
else:
    print("Unable to connect to wifi")
    print("Please check wifi credentials")
    dh.draw_multiline_text(tft, script_font,
                           ("No wifi", "Check credentials"))  # refactor to print expected wifi networks
    while True:
        pass  # hang on inability to connect

# Update time
if rtc.datetime()[0] < 2023:  # indicates unsuccessful update
    while True:
        update_ntptime("")
        if rtc.datetime()[0] >= 2023:
            break
        time.sleep(10)

print(f"Current rtc info: {rtc.datetime()}")

tm = rtc.datetime()
dh.draw_multiline_text(tft, script_font, (f"Date: {tm[1]}/{tm[2]}/{tm[0]}", f"Time (Z): {tm[4]}:{tm[5]}"))
time.sleep(3)

# Register with server
code, payload = server_tools.register_device()

print(f"Init reg resp: {code}")

if code == 200:
    room_id = payload["room_id"]
    unit_name = payload["display"]
    time_offset = payload["offset"]

    dh.draw_multiline_text(tft, script_font, (f"Unit name: {unit_name}",))
    time.sleep(15)
    tft.fill(BLACK)
else:
    while True:
        code, payload = server_tools.register_device()

        if code in (201, 401):
            dh.draw_multiline_text(tft, script_font, ("Registered as:", f"{wlan.config('mac').hex()}"))
        elif code == 200:
            break
        else:
            dh.draw_multiline_text(tft, script_font, ("Please contact", "manufacturer"))

        time.sleep(30)

tft.deinit()

timer_ntp = Timer(0)
timer_ntp.init(mode=Timer.PERIODIC, period=NTP_UPDATE_PERIOD, callback=update_ntptime)

last_check = 0

res_end = -1  # set to
active_reservation = False

while True:
    _, _, _, _, hr, mins, _, _ = rtc.datetime()  # (year, month, day, weekday, hours, minutes, seconds, subseconds)
    # check for an active reservation
    if mins in RESERVATION_CHECK_MINUTES and time.ticks_diff(time.ticks_ms(), last_check) > RESERVATION_CHECK_LOCKOUT:
        code, payload = server_tools.check_reservation()
        if code == 200:
            last_check = time.ticks_ms()
            print(f"Periodic check result: {payload}")
            res_end = payload["end"]
            if res_end >= 0:  # -1 is value if no reservation exists
                active_reservation = True
        else:
            print("Error connecting to server")  # Update display if it errors out?
            time.sleep_ms(500)  # don't constantly try to ping the server

    # reservation end {'end': 1691772300} - this payload was for GMT checkout time

    # TODO: Add checking within loop to break out if reservation is extended (not needed now)
    if active_reservation and res_end - current_epoch() < 330:  # verify units and math associated with this 5.5 minutes
        tft.init()

        # Update display inside for 5.5 minutes remaining
        while True:
            time_left = res_end - current_epoch()  # in seconds
            if time_left <= 0 and active_reservation:
                print("Please leave the space.")
                print("Draw red screen.")
                dh.draw_multiline_text(tft, script_font, ("Please", "Checkout"), fill=RED)
                code, payload = server_tools.check_reservation()
                if code == 200:
                    if payload["end"] == -1:
                        active_reservation = False
                        tft.fill(st7789.BLACK)
                        break
                    else:
                        res_end = payload["end"]
                time.sleep(30)  # prevents constant ping of server when not checked out
            elif 50 < (time_left % 60) < 60:
                print(f"Draw display with {time_left // 60} bars")
                dh.draw_bars(tft, time_left // 60)
                code, payload = server_tools.check_reservation()
                if code == 200:
                    if payload["end"] == -1:
                        active_reservation = False
                        break
                    else:
                        res_end = payload["end"]
                time.sleep(10)  # prevents multiple calls to server at rollover of minute
            elif 28 < (time_left % 60) < 32 or 13 < (time_left % 60) < 17:
                code, display = server_tools.check_reservation()
                if code == 200:
                    if payload["end"] == -1:
                        active_reservation = False
                        tft.fill(st7789.BLACK)
                        break
                    else:
                        res_end = payload["end"]
        tft.deinit()
