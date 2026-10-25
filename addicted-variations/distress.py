import sys, numpy as np
from PIL import Image, ImageFilter, ImageDraw, ImageOps, ImageFont
src, out = sys.argv[1], sys.argv[2]
base = Image.open(src).convert("RGB")
W, H = base.size
rng = np.random.default_rng(7)

def noise(scale, seed):
    r = np.random.default_rng(seed)
    small = Image.fromarray((r.random((max(2,H//scale), max(2,W//scale)))*255).astype(np.uint8))
    big = small.resize((W, H), Image.BICUBIC).filter(ImageFilter.GaussianBlur(max(1, scale*0.6)))
    return np.asarray(ImageOps.autocontrast(big), dtype=np.float32)/255

def fbm(seed):
    return (noise(160,seed)*.5 + noise(40,seed+1)*.3 + noise(8,seed+2)*.2)

def blur(a, r):
    return np.asarray(Image.fromarray((np.clip(a,0,1)*255).astype(np.uint8)).filter(ImageFilter.GaussianBlur(r)), dtype=np.float32)/255

def distress_mask(seed, strength=1.0):
    """1 = ink worn away to paper"""
    f = fbm(seed)
    f = f + (noise(3, seed+9)-.5)*0.18  # ragged edges
    blotch = np.clip((f - (0.70 - 0.04*strength)) * 7, 0, 1)
    fine = np.clip((noise(2, seed+11) - 0.86) * 8, 0, 1) * (fbm(seed+12) > 0.5)
    r = np.random.default_rng(seed+10)
    speck = (r.random((H, W)) > 1 - 0.006*strength).astype(np.float32)
    speck = np.clip(blur(speck, 0.8)*3, 0, 1) * (noise(30, seed+3) > 0.45)
    # scratches
    img = Image.new("L", (W, H), 0); d = ImageDraw.Draw(img)
    for _ in range(int(60*strength)):
        x, y = r.integers(0, W), r.integers(0, H)
        ang = r.normal(np.pi/2, 0.25) if r.random() < .7 else r.uniform(0, np.pi)
        L = r.integers(30, 400)
        d.line([(x, y), (x+np.cos(ang)*L, y+np.sin(ang)*L)], fill=int(r.integers(90, 230)), width=int(r.integers(1, 3)))
    scratch = np.asarray(img, dtype=np.float32)/255
    # fold creases
    crease = np.zeros((H, W), np.float32)
    for x in (W//2,): crease[:, max(0,x-2):x+2] = 0.9
    for y in (H//2,): crease[max(0,y-2):y+2, :] = 0.9
    crease = blur(crease, 1.5) * (0.4 + 0.6*noise(12, seed+4))
    # edge wear
    yy, xx = np.mgrid[0:H, 0:W]
    edge = np.minimum.reduce([xx, yy, W-1-xx, H-1-yy]).astype(np.float32)
    edge_w = np.clip(1 - (edge + noise(6, seed+5)*45) / 40, 0, 1)
    m = np.maximum.reduce([blotch*0.8, fine*0.7, speck, scratch*0.8, crease, edge_w])
    return np.clip(m*strength, 0, 1)

def apply(img, seed=1, paper=(232, 222, 196), strength=1.0, grain=0.07, fade=0.10, warm=True):
    a = np.asarray(img, dtype=np.float32)/255
    paper_c = np.array(paper, np.float32)/255
    # fade toward paper + warm yellowing
    a = a*(1-fade) + paper_c*fade
    if warm: a = a*np.array([1.03, 1.0, 0.92])
    # paper fiber texture
    fiber = (noise(2, seed+20)-.5)*0.05 + (noise(1, seed+21)-.5)*grain
    a = a + fiber[..., None]
    # uneven ink density
    a = a * (0.92 + 0.12*fbm(seed+30)[..., None])
    m = distress_mask(seed, strength)[..., None]
    paper_tex = paper_c * (0.9 + 0.15*noise(3, seed+40)[..., None])
    a = a*(1-m) + paper_tex*m
    # vignette
    yy, xx = np.mgrid[0:H, 0:W]
    v = ((xx/W-.5)**2 + (yy/H-.5)**2)
    a = a * (1 - 0.35*v)[..., None]
    return Image.fromarray((np.clip(a, 0, 1)*255).astype(np.uint8))

# --- background recolor helpers ---
hsv = np.asarray(base.convert("HSV"), dtype=np.float32)
h, s, v = hsv[...,0]/255*360, hsv[...,1]/255, hsv[...,2]/255
bgmask = ((h > 200) & (h < 260) & (s > 0.55) & (v < 0.45)).astype(np.float32)
bgmask = blur(bgmask, 1.2)[..., None]
lum = np.asarray(base.convert("L"), dtype=np.float32)[..., None]/255

def recolor(color):
    a = np.asarray(base, dtype=np.float32)/255
    c = np.array(color, np.float32)/255
    ref = lum.mean() if False else 0.12
    tinted = np.clip(c * (lum/ref) , 0, 1)
    return Image.fromarray((np.clip(a*(1-bgmask) + tinted*bgmask, 0, 1)*255).astype(np.uint8))

def sepia(img):
    g = np.asarray(ImageOps.autocontrast(img.convert("L"), cutoff=1), dtype=np.float32)/255
    lo, hi = np.array([40, 22, 12])/255, np.array([245, 225, 185])/255
    a = lo + (hi-lo)*g[..., None]
    return Image.fromarray((a*255).astype(np.uint8))

def duotone(img, dark, light, dot=6):
    g = img.convert("L")
    # halftone via rotated dot screen
    gr = np.asarray(g, dtype=np.float32)/255
    yy, xx = np.mgrid[0:H, 0:W].astype(np.float32)
    t = np.deg2rad(45); u = xx*np.cos(t)+yy*np.sin(t); w = -xx*np.sin(t)+yy*np.cos(t)
    screen = (np.cos(2*np.pi*u/dot)*np.cos(2*np.pi*w/dot)+1)/2
    ht = np.clip((gr - screen)*6 + .5, 0, 1)
    ht = ht*0.6 + gr*0.4
    d, l = np.array(dark)/255, np.array(light)/255
    return Image.fromarray(((d + (l-d)*ht[..., None])*255).astype(np.uint8))

def misregister(img, dx=4, dy=2):
    r, g, b = img.split()
    r = r.transform(img.size, Image.AFFINE, (1,0,-dx,0,1,-dy))
    return Image.merge("RGB", (r, g, b))

variants = {
  "01-navy-classic-distressed":  apply(base, 1),
  "02-burgundy-velvet":          apply(recolor((110, 14, 30)), 2),
  "03-emerald-art-deco":         apply(recolor((10, 70, 50)), 3),
  "04-noir-black-gold":          apply(recolor((22, 20, 22)), 4, strength=1.15),
  "05-sepia-playbill":           apply(sepia(base), 5, fade=0.05, strength=1.1),
  "06-duotone-halftone-gold":    apply(duotone(base, (18, 22, 70), (245, 205, 110)), 6, fade=0.04),
  "07-riso-misprint-pink":       apply(misregister(duotone(base, (90, 15, 60), (255, 190, 200), 5), 5, 3), 7, strength=1.2),
  "08-sunbleached-70s":          apply(Image.blend(recolor((30, 70, 140)), Image.new("RGB", base.size, (250, 200, 140)), 0.12), 8, fade=0.16, strength=1.3),
}
for k, im in variants.items():
    im.save(f"{out}/{k}.jpg", quality=92)

# contact sheet
tw = 400; th = int(H*tw/W); pad = 20
sheet = Image.new("RGB", (4*tw+5*pad, 2*th+3*pad), (20, 18, 18))
for i, im in enumerate(variants.values()):
    sheet.paste(im.resize((tw, th), Image.LANCZOS), (pad+(i%4)*(tw+pad), pad+(i//4)*(th+pad)))
sheet.save(f"{out}/00-contact-sheet.jpg", quality=90)
