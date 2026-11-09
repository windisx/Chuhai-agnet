"""以已生成素材制作持续循环的首页动效预览，不更新网站背景。"""
from pathlib import Path
import math
import sys
import numpy as np
from PIL import Image, ImageDraw, ImageFont, ImageOps

BASE = Path(__file__).resolve().parent
OUTPUT = Path(sys.argv[1]) if len(sys.argv) > 1 else BASE / 'fleet-home-preview.gif'
W, H = 960, 540
sea = ImageOps.fit(Image.open(BASE / 'sea.png').convert('RGB'), (W, H))
assets = {}
for name, trim in [('boat', .99), ('cruise', .97), ('cargo', .9)]:
    asset = Image.open(BASE / (name + '.png')).convert('RGBA')
    asset = asset.crop(asset.getbbox())
    assets[name] = asset.crop((0, 0, asset.width, int(asset.height * trim)))
FONT_DIR = Path(sys.argv[2]) if len(sys.argv) > 2 else BASE
regular = str(FONT_DIR / 'regular.ttc' if (FONT_DIR / 'regular.ttc').is_file() else Path('C:/Windows/Fonts/msyh.ttc'))
bold = str(FONT_DIR / 'bold.ttc' if (FONT_DIR / 'bold.ttc').is_file() else Path('C:/Windows/Fonts/msyhbd.ttc'))
font = lambda size, heavy=False: ImageFont.truetype(bold if heavy else regular, size)
arr = np.asarray(sea)
yy, xx = np.mgrid[0:H, 0:W]
strength = np.clip((yy / H - .43) / .57, 0, 1)
ships = [
    ('boat', 60, 472, 82, 0, 1, 1),
    ('cargo', 340, 465, 188, 1.8, .3, 1),
    ('cruise', 635, 505, 220, 3.7, .45, -1),
    ('boat', 860, 450, 42, 5, .8, 1),
]
sprites = []
for kind, _, _, width, _, _, direction in ships:
    source = assets[kind]
    sprite = source.resize((width, int(width * source.height / source.width)), Image.Resampling.LANCZOS)
    sprites.append(ImageOps.mirror(sprite) if direction < 0 else sprite)
overlay = Image.new('RGBA', (W, H))
draw = ImageDraw.Draw(overlay)
for y in range(H):
    a = int(48 * max(0, 1-y/H))
    draw.line((0,y,W,y), fill=(255,255,255,a))
draw.text((28,22), '链证出海', font=font(19,True), fill='#18354c')
def center(y, value, f, color):
    width = draw.textlength(value,font=f)
    draw.text(((W-width)/2,y),value,font=f,fill=color)
center(122,'出海资料预审智能体',font(11),'#39556a')
center(164,'资料有据，出海有序。',font(42,True),'#18344d')
center(230,'核对产品资料，追溯证据来源，理清补件事项。',font(13),'#36516a')
draw.rounded_rectangle((418,280,542,319),radius=20,fill='#2465e9')
center(290,'开始体验  →',font(13),'white')
center(517,'链证出海 · 辅助资料预审',font(9),'#edf5fc')
draw.text((18,519),'动态预览 · 持续循环',font=font(8),fill='#edf5fc')
frames=[]
for n in range(80):
    phase=math.tau*n/80
    sx=np.clip((xx+np.sin(yy*.04-phase)*strength*1.1).astype(int),0,W-1)
    sy=np.clip((yy+np.sin(xx*.026+phase)*strength*.7).astype(int),0,H-1)
    image=Image.fromarray(arr[sy,sx]).convert('RGBA')
    for (_, x, y, _, offset, response, direction), sprite in zip(ships, sprites):
        bx=int(x+3*math.sin(phase+offset))
        by=int(y+response*(math.sin(phase+offset)+.3*math.sin(phase*2+offset)))
        wake=Image.new('RGBA',(W,H));wd=ImageDraw.Draw(wake)
        stern=bx if direction > 0 else bx+sprite.width
        for i in range(1,30):
            trail=stern-direction*i*1.4
            alpha=int(40*(1-i/30))
            wd.line((trail,by+2,trail-direction*3,by+2+i*.06),fill=(236,249,255,alpha),width=1)
        image.alpha_composite(wake)
        reflected=ImageOps.flip(sprite).resize((sprite.width,max(1,int(sprite.height*.12))))
        alpha=reflected.getchannel('A').point(lambda a:int(a*.06))
        reflected.putalpha(alpha)
        image.alpha_composite(reflected,(bx,by+2))
        rotated=sprite.rotate((math.sin(phase+offset)+.2*math.sin(phase*2+offset))*.3*response,resample=Image.Resampling.BICUBIC,expand=True)
        image.alpha_composite(rotated,(bx,by-rotated.height))
    image.alpha_composite(overlay)
    frames.append(image.convert('RGB').quantize(colors=128))
frames[0].save(OUTPUT,save_all=True,append_images=frames[1:],duration=125,loop=0,disposal=2)
with Image.open(OUTPUT) as check:
    assert check.n_frames==80 and check.info.get('loop')==0
print('Created 80-frame continuously looping fleet GIF preview')
