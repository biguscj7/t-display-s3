import mytime as ntptime
from machine import RTC, Timer, reset
import wifimgr
import time
import tft_config
import st7789
import romans as script_font
import display_helpers as dh
import server_tools
import gc

gc.collect()

NTP_TO_UNIX = 946684800  # needed to convert ntptime.time() to normal UNIX timestamp

NTP_UPDATE_PERIOD = 3600 * 1000 * 6  # milliseconds in an hour * hours
RES_UPDATE_PERIOD = 1000 * 15  # milliseconds in 15 seconds

RESERVATION_CHECK_MINUTES = (9, 24, 39, 54)
RESERVATION_CHECK_LOCKOUT = 60000

QW_BLUE = st7789.color565(48, 89, 151)
ORANGE = st7789.color565(255, 109, 10)
BLACK = st7789.BLACK
WHITE = st7789.WHITE
RED = st7789.RED

rtc = RTC()

tft = tft_config.config(1)
tft.init()  # init for boot sequence
tft.offset(1, 35)  # offset for config 1

tft.fill(QW_BLUE)


def update_ntptime(t):
    try:
        ntptime.settime()
        print("Attempted ntp update")
    except OSError as e:
        print(f"Time update error: {e}")  # add to display
        # quick_display(("Failed time update", str(e)), 1.0, color=ORANGE)


def current_epoch():
    return time.time() + NTP_TO_UNIX


def display_init_deinit(func):
    def wrapper(*args, **kwargs):
        tft.init()
        func(*args, **kwargs)
        tft.deinit()

    return wrapper


@display_init_deinit
def quick_display(lines, hold_time=3, font_scale=2.0, color=QW_BLUE):
    dh.draw_multiline_text(tft, script_font, lines, fill=color, start_scale=font_scale)
    time.sleep(hold_time)
    welcome_display()


def welcome_display():
    dh.draw_multiline_text(tft, script_font, ("Welcome to the", "Quiet Workplace"), fill=QW_BLUE, start_scale=1.75)


# Config wifi
wlan_sta = wifimgr.get_connection()

if wlan_sta is not None:
    dh.draw_multiline_text(tft, script_font,
                           ("Connected to:", f"{wlan_sta.config('ssid')}", f"Signal str: {wlan_sta.status('rssi')}"))
    time.sleep(2)
else:
    print("Unable to connect to wifi. Check credentials")
    dh.draw_multiline_text(tft, script_font,
                           ("No wifi", "Check credentials"))  # refactor to print expected wifi networks
    while True:
        pass  # hang on inability to connect

# Update time
if time.gmtime()[0] < 2023:  # indicates unsuccessful update
    while True:
        update_ntptime("")
        if time.gmtime()[0] >= 2023:
            break
        time.sleep(10)

print(f"Current time info: {time.gmtime()}")

tm = time.gmtime()
dh.draw_multiline_text(tft, script_font, (f"Date: {tm[1]}/{tm[2]}/{tm[0]}", f"Time (Z): {tm[3]}:{tm[4]}"),
                       start_scale=1.75)
time.sleep(2)

# Register with server
code, payload = server_tools.register_device()

print(f"Registration response code: {code}")

if code == 200:
    room_id = payload["room_id"]
    unit_name = payload["display"]
    time_offset = payload["offset"]

    dh.draw_multiline_text(tft, script_font, (f"Unit name: {unit_name}",))
    print(f"Unit name: {unit_name}")
    time.sleep(5)
else:
    while True:
        code, payload = server_tools.register_device()

        if code in (201, 401):
            dh.draw_multiline_text(tft, script_font, ("Registered as:", f"{wlan_sta.config('mac').hex()}"))
        elif code == 200:
            break
        elif code == 999:
            dh.draw_multiline_text(tft, script_font, ("Failed registration", "retrying...."))
            gc.collect()
        else:
            dh.draw_multiline_text(tft, script_font, ("Please contact", "manufacturer"))

        time.sleep(30)

welcome_display()
tft.deinit()  # deinit after boot sequence

timer_ntp = Timer(0)
timer_ntp.init(mode=Timer.PERIODIC, period=NTP_UPDATE_PERIOD, callback=update_ntptime)

last_check = 0

res_end = -1  # set to
active_reservation = False

while True:
    _, _, _, hr, mins, sec, _, _ = time.gmtime()  # (2023, 8, 21, 18, 42, 41, 0, 233)

    # check for an active reservation
    if hr == 2 and mins == 0 and 0 < sec < 10:
        print("doing a reset")
        reset()

    if (mins in RESERVATION_CHECK_MINUTES and time.ticks_diff(time.ticks_ms(),
                                                              last_check) > RESERVATION_CHECK_LOCKOUT) or last_check == 0:
        print(f"Hours: {hr}\nMinutes:{mins}")
        if wifimgr.get_connection() is None:
            print("No wifi connection")
            quick_display(("No wifi", "connection"), 3.0, color=ORANGE)

        code, payload = server_tools.check_reservation()
        if code == 200:
            last_check = time.ticks_ms()
            print(f"Periodic check result: {payload}")
            res_end = payload["end"]
            if res_end >= 0:  # -1 is value if no reservation exists
                active_reservation = True
                time_left = res_end - current_epoch()  # in seconds
        else:
            print("----------Error checking reservation--------------")
            print(f"Server code: {code}")
            print(f"Server text: {payload}")
            quick_display((code, payload), 1.0, color=ORANGE)

    # TODO: Add checking within loop to break out if reservation is extended (not needed now)
    if active_reservation and res_end - current_epoch() < 330:  # 5.5 minutes
        gc.collect()
        red_flag = False
        need_init = True
        print("Entering active res loop")

        # Update display inside for 5.5 minutes remaining
        while True:
            if (44 < (time_left % 60) < 46) or (29 < (time_left % 60) < 31) or (14 < (time_left % 60) < 16):
                print("Pinging server on the 15 second interval.")
                if wifimgr.get_connection() is None:
                    print("No wifi connection")
                    quick_display(("No wifi", "connection"), 3.0, color=ORANGE)

                code, payload = server_tools.check_reservation()
                if code == 200:
                    if payload["end"] == -1:
                        active_reservation = False
                        red_flag = False
                        print("Blanking and deinit display.")
                        break
                    else:
                        res_end = payload["end"]
                elif code == 999:
                    print(f"Error in active loop call: {payload}")
                    quick_display((code, payload), 1.0, color=ORANGE)
                time_left = res_end - current_epoch()  # in seconds

            if time_left <= -30 and active_reservation:
                if not red_flag:
                    print("Draw red screen.")
                    if need_init:
                        tft.init()
                        need_init = False
                    dh.draw_multiline_text(tft, script_font, ("Please", "Checkout"), fill=RED)
                red_flag = True
            elif -30 < time_left <= 0:
                print("Buffer of 30 seconds before red flash")
                if need_init:
                    tft.init()
                    need_init = False
                tft.fill(QW_BLUE)
                time.sleep(5)
            elif 55 < (time_left % 60) < 60 and time_left > 0:
                print(f"Draw display with {(time_left // 60) + 1} bars")
                if need_init:
                    tft.init()
                    need_init = False
                dh.draw_bars(tft, (time_left // 60) + 1)
                time.sleep(5)

        welcome_display()
        tft.deinit()
