"""Genera un'anteprima PNG del display LCD per il README."""

from __future__ import annotations

from pathlib import Path

from PIL import Image, ImageDraw, ImageFont

OUT = Path(__file__).resolve().parent / "assets" / "preview-lcd.png"

BG_APP = (232, 230, 225)
FRAME_PLASTIC = (244, 242, 237)
FRAME_EDGE = (201, 197, 188)
LCD_BG = (200, 210, 184)
LCD_DIM = (168, 180, 152)
LCD_INK = (26, 34, 20)
LCD_FAINT = (154, 171, 136)
SHADOW = (0, 0, 0, 40)


def font(size: int, bold: bool = False) -> ImageFont.FreeTypeFont | ImageFont.ImageFont:
    candidates = [
        r"C:\Windows\Fonts\consolab.ttf" if bold else r"C:\Windows\Fonts\consola.ttf",
        r"C:\Windows\Fonts\arialbd.ttf" if bold else r"C:\Windows\Fonts\arial.ttf",
    ]
    for path in candidates:
        try:
            return ImageFont.truetype(path, size)
        except OSError:
            continue
    return ImageFont.load_default()


def draw_face(draw: ImageDraw.ImageDraw, cx: int, cy: int, r: int = 22) -> None:
    draw.ellipse((cx - r, cy - r, cx + r, cy + r), outline=LCD_INK, width=3)
    draw.ellipse((cx - 9, cy - 7, cx - 4, cy - 2), fill=LCD_INK)
    draw.ellipse((cx + 4, cy - 7, cx + 9, cy - 2), fill=LCD_INK)
    # smile
    draw.arc((cx - 11, cy - 2, cx + 11, cy + 14), start=20, end=160, fill=LCD_INK, width=3)


def draw_signal(draw: ImageDraw.ImageDraw, x0: int, y0: int, levels: int = 4) -> None:
    for i in range(4):
        h = 6 + i * 5
        x = x0 + i * 9
        color = LCD_INK if i < levels else LCD_FAINT
        draw.rectangle((x, y0 - h, x + 5, y0), fill=color)


def main() -> None:
    W, H = 920, 560
    img = Image.new("RGB", (W, H), BG_APP)
    draw = ImageDraw.Draw(img)

    # soft vignette / card shadow
    card = (120, 70, 800, 470)
    shadow_box = (card[0] + 10, card[1] + 14, card[2] + 10, card[3] + 14)
    draw.rounded_rectangle(shadow_box, radius=28, fill=(210, 208, 202))
    draw.rounded_rectangle(card, radius=28, fill=FRAME_PLASTIC, outline=FRAME_EDGE, width=3)

    # LCD glass
    lcd = (180, 120, 740, 420)
    draw.rounded_rectangle(lcd, radius=18, fill=LCD_BG, outline=LCD_DIM, width=3)
    draw.rounded_rectangle((190, 130, 730, 410), radius=12, fill=LCD_BG, outline=LCD_FAINT, width=1)

    # signal bars
    draw_signal(draw, 220, 175, levels=4)

    # temperature
    f_temp = font(96, bold=True)
    f_unit = font(28, bold=True)
    f_hum = font(40, bold=True)
    f_ui = font(22, bold=True)
    f_small = font(18)

    temp = "23.4"
    # center-ish temp
    draw.text((300, 195), temp, fill=LCD_INK, font=f_temp)
    draw.text((620, 210), "°C", fill=LCD_INK, font=f_unit)
    draw.text((655, 155), "⌁", fill=LCD_INK, font=f_ui)

    # humidity + face
    draw.text((230, 345), "48%", fill=LCD_INK, font=f_hum)
    draw_face(draw, 620, 360, r=26)

    # caption under card
    title = "Modalità Solo LCD — temperatura, umidità, segnale BLE e comfort"
    tw = draw.textlength(title, font=f_small)
    draw.text(((W - tw) / 2, 500), title, fill=(90, 90, 82), font=f_small)

    OUT.parent.mkdir(parents=True, exist_ok=True)
    img.save(OUT, "PNG", optimize=True)
    print(OUT)


if __name__ == "__main__":
    main()
