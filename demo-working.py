import machine
import time
import tft_config
import st7789
import romans as script_font
import display_helpers as dh
import gc

gc.collect()

button14 = machine.Pin(14, machine.Pin.IN, machine.Pin.PULL_UP)
button0 = machine.Pin(0, machine.Pin.IN, machine.Pin.PULL_UP)

QW_BLUE = st7789.color565(48, 89, 151)
ORANGE = st7789.color565(255, 109, 10)
BLACK = st7789.BLACK
WHITE = st7789.WHITE
RED = st7789.RED

tft = tft_config.config(1)
tft.offset(1, 35)  # offset for config 1


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
    tft.fill(BLACK)


@display_init_deinit
def set_display(lines, font_scale=2.0, color=QW_BLUE):
    dh.draw_multiline_text(tft, script_font, lines, fill=color, start_scale=font_scale)


set_display(("Welcome to the", "Quiet Workplace"), font_scale=1.75)

while True:
    if button14.value() == 0 or button0.value() == 0:
        tft.init()
        print("Starting display loop")

        for i in (5, 4, 3, 2, 1):
            dh.draw_bars(tft, i)
            print(f"Drawing {i} bars")
            time.sleep(0.5)

        tft.deinit()

        print("Filling blue")
        quick_display(("", ""), 5)

        print("Showing please checkout")
        quick_display(("Please", "Checkout"), 5, font_scale=2, color=RED)

        set_display(("Welcome to the", "Quiet Workplace"), font_scale=1.75)

        tft.deinit()
