"""Create an original test frame; no game artwork or dialogue is used."""

from pathlib import Path

from PIL import Image, ImageDraw, ImageFont


ROOT = Path(__file__).resolve().parent
image = Image.new("RGB", (1280, 720), "#293441")
draw = ImageDraw.Draw(image)
for y in range(0, 580, 3):
    shade = int(41 + 20 * y / 580)
    draw.line((0, y, 1280, y), fill=(shade, shade + 11, shade + 21))
draw.rectangle((0, 575, 1279, 719), fill="#111a26")
draw.line((0, 615, 1280, 615), fill="#688b9d", width=2)
font_path = Path(r"C:\Windows\Fonts\msyh.ttc")
font = ImageFont.truetype(str(font_path), 28)
small = ImageFont.truetype(str(font_path), 19)
draw.text((54, 42), "剧情配音演示画面", font=font, fill="#dbe7ef")
draw.text((54, 89), "模拟画面 · 与游戏文件无关", font=small, fill="#a9bbc9")
draw.text((230, 638), "特菲", font=font, fill="#f0f4f6")
draw.text((388, 638), "你好，这是一段剧情配音演示。", font=font, fill="#f0f4f6")
image.save(ROOT / "演示截图.png")
