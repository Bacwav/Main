import sys, numpy as np
from PIL import Image, ImageDraw, ImageFilter
design_path, out_path = sys.argv[1], sys.argv[2]
W, H, S = 2000, 2400, 2
rng = np.random.default_rng(3)
yy, xx = np.mgrid[0:H, 0:W].astype(np.float32)

def mask(shapes, b=1.2):
    m = Image.new("L", (W*S, H*S), 0); d = ImageDraw.Draw(m)
    for kind, pts in shapes:
        if kind == "poly": d.polygon([(x*S, y*S) for x, y in pts], fill=255)
        else: d.ellipse([v*S for v in pts], fill=255)
    return np.asarray(m.resize((W, H), Image.LANCZOS).filter(ImageFilter.GaussianBlur(b)), np.float32)/255

def blur(a, r):
    return np.asarray(Image.fromarray((np.clip(a, 0, 1)*255).astype(np.uint8)).filter(ImageFilter.GaussianBlur(r)), np.float32)/255

def lines(segs, b):
    im = Image.new("L", (W, H), 0); d = ImageDraw.Draw(im)
    for p, w, v in segs: d.line(p, fill=v, width=w, joint="curve")
    return blur(np.asarray(im, np.float32)/255, b)

def noise(scale, seed):
    r = np.random.default_rng(seed)
    sm = Image.fromarray((r.random((max(2, H//scale), max(2, W//scale)))*255).astype(np.uint8))
    return np.asarray(sm.resize((W, H), Image.BICUBIC).filter(ImageFilter.GaussianBlur(max(1, scale*.5))), np.float32)/255

mirror = lambda pts: [(W-x, y) for x, y in pts]

# ---------- silhouette ----------
hood = mask([("poly", [(700,600),(690,420),(740,300),(850,225),(1000,200),(1150,225),(1260,300),(1310,420),(1300,600)])])
slv = [(640,500),(470,560),(400,800),(340,1300),(285,1860),(470,1880),(520,1400),(575,1000),(600,800)]
sleeveL, sleeveR = mask([("poly", slv)]), mask([("poly", mirror(slv))])
cf = [(282,1850),(472,1870),(466,2005),(276,1990)]
cuffL, cuffR = mask([("poly", cf)]), mask([("poly", mirror(cf))])
body = mask([("poly", [(790,470),(620,500),(575,700),(590,1100),(595,1500),(590,1925),(1410,1925),(1405,1500),(1410,1100),(1425,700),(1380,500),(1210,470)])])
band = mask([("poly", [(590,1910),(1410,1910),(1414,2075),(586,2075)])])
sil = np.maximum.reduce([hood, sleeveL, sleeveR, cuffL, cuffR, body, band])

# hood opening (inside lining visible) and crossover flaps forming a V at the neck
opening = mask([("poly", [(830,600),(820,430),(880,330),(1000,300),(1120,330),(1180,430),(1170,600),(1000,700)])], 2)
flapL = mask([("poly", [(760,560),(830,600),(1000,700),(1030,690),(1000,730),(880,700),(780,640)])], 1.5)
flapR = mask([("poly", mirror([(760,560),(830,600),(1000,700),(1030,690),(1000,730),(880,700),(780,640)]))], 1.5)

# ---------- fabric shading (value map) ----------
v = np.full((H, W), 0.115, np.float32)
v *= 1.0 + 0.45*np.exp(-(((xx-850)/650)**2 + ((yy-850)/850)**2))        # key light upper-left
# rounded form: darken towards each part's outline
for part, r, k in [(body, 60, .45), (sleeveL, 40, .5), (sleeveR, 40, .5), (hood, 50, .45)]:
    rim = np.clip(part - blur(part*0.999, r)*1.0, 0, 1)
    v *= 1 - k*rim*2
# sleeve/body overlap shadows and highlights
gap = mask([("poly", [(575,760),(610,760),(595,1900),(500,1890)])], 16) + mask([("poly", mirror([(575,760),(610,760),(595,1900),(500,1890)]))], 16)
v *= 1 - 0.6*np.clip(gap, 0, 1)
# hood interior darker, cast shadow under hood onto chest
v = v*(1-opening) + (0.055 + 0.07*np.clip((yy-300)/400, 0, 1))*opening
v *= 1 - 0.30*blur(mask([("poly", [(760,560),(1240,560),(1180,740),(820,740)])]), 40)*(1-opening)
v = v*(1-np.maximum(flapL, flapR)) + v*1.25*np.maximum(flapL, flapR)
# folds: highlight ridge + shadow valley pairs
segs_hi, segs_lo = [], []
for _ in range(22):
    s = rng.choice([-1, 1]); x = 1000 + s*rng.uniform(450, 640); y = rng.uniform(650, 1780)
    p = [(x, y), (x + s*rng.uniform(30, 90), y + rng.uniform(50, 140))]
    segs_hi.append((p, int(rng.uniform(6, 14)), int(rng.uniform(120, 230))))
    segs_lo.append(([(a+s*14, b+10) for a, b in p], int(rng.uniform(8, 16)), int(rng.uniform(120, 220))))
for _ in range(16):
    x = rng.uniform(640, 1360); y = rng.uniform(1860, 1905)
    p = [(x, y), (x + rng.uniform(-40, 40), y - rng.uniform(80, 240))]
    segs_hi.append((p, int(rng.uniform(8, 18)), int(rng.uniform(90, 180))))
    segs_lo.append(([(a+16, b) for a, b in p], int(rng.uniform(8, 16)), int(rng.uniform(100, 200))))
for x0 in (720, 1280):  # soft chest-to-hip drape
    segs_hi.append(([(x0, 1150), (x0 + (x0-1000)*0.05, 1700)], 40, 70))
v *= 1 + 0.55*lines(segs_hi, 9) - 0.45*lines(segs_lo, 9)
# seams: shoulder, armhole, waistband, cuffs, pocket, flaps
seam_pts = [
    ([(790,470),(640,500)], 3, 255), ([(1210,470),(1360,500)], 3, 255),
    ([(640,500),(600,800),(590,1100)], 3, 200), ([(1360,500),(1400,800),(1410,1100)], 3, 200),
    ([(590,1912),(1410,1912)], 4, 255), ([(282,1855),(472,1872)], 4, 255), ([(W-282,1855),(W-472,1872)], 4, 255),
    ([(760,1470),(1240,1470)], 3, 230), ([(760,1470),(670,1880)], 3, 230), ([(1240,1470),(1330,1880)], 3, 230),
    ([(1000,700),(1000,730)], 3, 255),
]
seams = lines(seam_pts, 2.2)
v *= 1 - 0.55*seams
v *= 1 + 0.30*np.roll(seams, 5, axis=0)  # stitched edge catches light
# kangaroo pocket: slightly raised, with shadowed side openings
pocket = mask([("poly", [(760,1470),(1240,1470),(1330,1880),(670,1880)])], 3)
v *= 1 + 0.08*pocket
v *= 1 - 0.5*lines([([(780,1500),(700,1800)], 16, 255), ([(1220,1500),(1300,1800)], 16, 255)], 10)*pocket
# rib knit
ribzone = np.maximum.reduce([cuffL, cuffR, band])
v *= 1 - ribzone*0.18*(0.5 + 0.5*np.sin(xx/3.2))
# fleece grain
v *= 0.92 + 0.16*np.random.default_rng(5).random((H, W)).astype(np.float32)
v = blur(v, 0.7)
fabric = np.stack([v*0.97, v*0.98, v*1.04], -1)

# ---------- print: faded, distressed edges ----------
design = Image.open(design_path).convert("RGB")
c = 45  # trim the poster's own worn paper border so it fades straight into fabric
design = design.crop((c, c, design.width - c, design.height - c))
pw = 610; ph = int(design.height*pw/design.width)
design = design.resize((pw, ph), Image.LANCZOS)
px, py = 1000 - pw//2, 790
art = np.zeros((H, W, 3), np.float32); art[py:py+ph, px:px+pw] = np.asarray(design, np.float32)/255
box = np.zeros((H, W), np.float32); ix, iy = 55, 85
box[py+iy:py+ph-iy, px+ix:px+pw-ix] = 1
soft = blur(box, 55)                                         # wide feathered falloff
grit = noise(5, 11)*0.55 + noise(2, 12)*0.45
alpha = np.clip((soft - 0.10 - (grit-0.5)*0.75*(1-soft)) * 1.8, 0, 1)   # grit only eats the fading zone
hard = np.zeros((H, W), np.float32); hard[py+4:py+ph-4, px+4:px+pw-4] = 1
alpha *= blur(hard, 6)                                       # never reach the art's cut edge
alpha *= 1 - 0.35*(np.random.default_rng(13).random((H, W)) > 0.93)  # cracked-ink dropout
alpha *= 0.94
# ink follows the fabric's light and folds
rel = v / np.median(v[py:py+ph, px:px+pw])
ink = art*0.92*np.clip(0.55 + 0.45*rel, 0.4, 1.35)[..., None]
ink = ink*0.9 + ink.mean(-1, keepdims=True)*0.1
fabric = fabric*(1-alpha[..., None]) + ink*alpha[..., None]

# drawstrings
strings = [([(905,640),(900,820),(892,1020)], 13, 255), ([(1095,640),(1100,820),(1108,1020)], 13, 255)]
dmask = lines(strings, 1.2)
sv = (0.07 + 0.10*lines([([(901,640),(896,1020)], 3, 255), ([(1091,640),(1104,1020)], 3, 255)], 1.5))
aglet = mask([("poly", [(884,1015),(901,1015),(899,1080),(886,1080)]), ("poly", [(1099,1015),(1116,1015),(1114,1080),(1101,1080)])], 1)
sv = sv*(1-aglet) + 0.18*(0.6 + 0.4*np.sin(xx/3))*aglet; dmask = np.maximum(dmask, aglet)
cast = blur(np.roll(np.roll(dmask, 6, 0), 5, 1), 4)
fabric *= 1 - 0.5*cast[..., None]*(1-dmask[..., None])
fabric = fabric*(1-dmask[..., None]) + np.stack([sv*0.97, sv*0.98, sv*1.04], -1)*dmask[..., None]

# ---------- backdrop ----------
g = 0.88 - 0.14*np.sqrt(((xx-1000)/1400)**2 + ((yy-1000)/1600)**2)
bg = np.stack([g, g*0.985, g*0.96], -1)
bg *= 1 - 0.32*blur(np.roll(np.roll(sil, 28, 0), 20, 1), 45)[..., None]
out = bg*(1-sil[..., None]) + fabric*sil[..., None]
Image.fromarray((np.clip(out, 0, 1)*255).astype(np.uint8)).save(out_path, quality=93)
