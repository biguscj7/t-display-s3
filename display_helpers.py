import time
import st7789

DISPLAY_HEIGHT = 170
DISPLAY_WIDTH = 320
WIDTH_BUFFER = 5
HEIGHT_BUFFER = 0

BARS = ((259, 40), (198, 65), (137, 90), (76, 115), (15, 140))

QW_BLUE = st7789.color565(48, 89, 151)
BLACK = st7789.BLACK
WHITE = st7789.WHITE
RED = st7789.RED


def dynamic_line(tft, font, line_text, scale_factor):
    start_len = tft.draw_len(font, line_text, scale_factor)

    if start_len <= (DISPLAY_WIDTH - WIDTH_BUFFER):
        return line_text, scale_factor, start_len
    else:
        for j in range(5):
            scale_factor -= 0.25
            scaled_len = tft.draw_len(font, line_text, scale_factor)
            if scaled_len <= (DISPLAY_WIDTH - WIDTH_BUFFER):
                return line_text, scale_factor, scaled_len

        for i in range(len(line_text), 0, -1):
            scaled_len = tft.draw_len(font, line_text[0:i], scale_factor)
            if scaled_len <= (DISPLAY_WIDTH - WIDTH_BUFFER):
                return line_text[0:i], scale_factor, scaled_len


def compute_centering_x(text_len):
    return int(165 - text_len * 0.5)


def draw_bars(tft, num_bars):
    tft.fill(QW_BLUE)
    for x, h in BARS[0:num_bars]:
        print("Add rect at: " + str(x) + ", " + str(15) + " height: " + str(h))
        tft.fill_rect(x, (150 - h), 49, h, WHITE)
    time.sleep(1)


def draw_multiline_text(tft, script_font, text_lines, fill=QW_BLUE, start_scale=2.0):
    if fill:
        tft.fill(fill)

    line_y = (25, 70, 120) if len(text_lines) == 3 else (50, 110)
    for idx, line in enumerate(text_lines):
        text, scale_factor, text_len = dynamic_line(tft, script_font, line, start_scale)
        first_line_x = compute_centering_x(text_len)
        tft.draw(script_font, text, first_line_x, line_y[idx], st7789.WHITE, scale_factor)
