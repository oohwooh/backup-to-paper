import argparse
from PIL import Image, ImageOps, ImageDraw, ImageFilter, ImageGrab
import math

def only_consecutive(data, n):
    out = set()
    run = set()
    if isinstance(data, set):
        data = tuple(data)
    for n1,n2 in zip(data, data[1:]): # compare consecutive numbers
        if n2 == n1+1: # consecutive
            run.add(n1)
            run.add(n2)
        else: # non-consecutive
            if len(run) >= n:
                [out.add(m) for m in run]
            run = set()
    if len(run) >= n:
        [out.add(m) for m in run]
    if not out:
        return data
    return out

def clean_image(fp):
    img = Image.open(fp, ).convert("RGB")
    img = ImageOps.posterize(img, 1)
    
    paper = max([c for _, c in img.getcolors()])
    ink = min(c for _, c in img.getcolors())
    paper_yx = {}
    paper_xy = {}
    ink_yx = {}

    for x in range(img.width):
        for y in range(img.height):
            px = img.getpixel((x, y))
            if(px == paper):
                paper_yx.setdefault(y, set())
                paper_yx[y].add(x)
                paper_xy.setdefault(x, set())
                paper_xy[x].add(y)
            if(px == ink):
                ink_yx.setdefault(y, set())
                ink_yx[y].add(x)

    for key in paper_yx:
        mn = min(only_consecutive(paper_yx[key], 8))
        mx = max(only_consecutive(paper_yx[key], 8))
        # for x in paper_yx[key]:
            # img.putpixel((x,key), (255,255,255))
        paper_yx[key] = [mn, mx, mx - mn]
    for key in paper_xy:
        mn = min(only_consecutive(paper_xy[key], 8))
        mx = max(only_consecutive(paper_xy[key], 8))
        # for x in paper_yx[key]:
            # img.putpixel((x,key), (255,255,255))
        paper_xy[key] = [mn, mx, mx - mn]
    paper_width = max(paper_yx[k][2] for k in paper_yx)
    paper_height = max(paper_xy[k][2] for k in paper_xy)

    out = Image.new('RGB', size=(img.width, img.height))
    for y in paper_yx:
        x1, x2, _ = paper_yx[y]
        out.paste(img.resize(size=(paper_width, 1), box=(x1, y, x2, y)), (0,y))
        # img.putpixel((x1, y), (255,255,255))
        # img.putpixel((x2, y), (255,255,255))
    # for x in paper_xy:
        # y1, y2, _ = paper_xy[x]
        # out.paste(img.resize(size=(1,paper_height), box=(x,y1,x,y2)), (x,0))
    out = ImageOps.grayscale(out)
    out = ImageOps.autocontrast(out)
    out = out.crop(out.getbbox())

    return out

def img_to_bits(img: Image.Image):
    draw = ImageDraw.Draw(img)
    PX_SIZE = 9
    data = []
    for y in range(0, img.height, PX_SIZE):
        data.append([])
        for x in range(0, img.width, PX_SIZE):
            if not (x+PX_SIZE > img.width or y+PX_SIZE > img.height):
                px = img.crop((x, y, x+PX_SIZE, y+PX_SIZE))
                if sum(px.resize((1,1)).getpixel((0,0))) < 510:
                    data[-1].append(True)
                    draw.rectangle((x,y,x+PX_SIZE,y+PX_SIZE), outline="GREEN")
                else:
                    data[-1].append(False)
                    draw.rectangle((x,y,x+PX_SIZE,y+PX_SIZE), outline="RED")
    data_flat = []
    for idx, row in enumerate(data):
        data_flat.extend(row[:-1])
        if(row.count(True) % 2 == 0):
            print(f'row {idx} OK')
        else:
            print(f'row {idx} FAIL')
    img.show()
    return [sum([(1 if c else 0)<<(i) for i,c in enumerate(byte)]) for byte in [data_flat[8*i:8*(i+1)] for i in range(len(data_flat)//8+1)]]
    # return data

if __name__ == "__main__":
    parser = argparse.ArgumentParser()

    parser.add_argument("to_decode", help="File to decode")
    parser.add_argument("-o", "--output", action="store", dest="output")

    args = parser.parse_args()

    cleaned = clean_image(args.to_decode)
    cleaned.save('out.png')

    bits = img_to_bits(Image.open(args.to_decode))
    print(bits)
    with open("o.json", "wb") as f:
        f.write(bytes(bits))
    