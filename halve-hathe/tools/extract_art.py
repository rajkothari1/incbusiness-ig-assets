# Extract hand-drawn cartoons from the cover photo as clean B/W bitmaps (2x scale)
import sys, numpy as np
from PIL import Image, ImageFilter, ImageOps
src = sys.argv[1]
S = 2
W, H = 1400*S, 2100*S
pts = [(165,46),(1300,26),(1432,1965),(222,1982)]
im = Image.open(src).convert('RGB')
out = [(0,0),(W,0),(W,H),(0,H)]
A=[];B=[]
for (x,y),(X,Y) in zip(pts,out):
    A.append([X,Y,1,0,0,0,-x*X,-x*Y]); B.append(x)
    A.append([0,0,0,X,Y,1,-y*X,-y*Y]); B.append(y)
c = np.linalg.solve(np.array(A,float),np.array(B,float))
big = im.transform((W,H), Image.PERSPECTIVE, c, Image.BICUBIC)
k = 1.05*S
boxes = {'dentist':(470,778,945,1200),'handstand':(128,1235,500,1725),'cricketer':(948,1180,1268,1740)}
for name,(x0,y0,x1,y1) in boxes.items():
    cr = big.crop((int(x0*k),int(y0*k),int(x1*k),int(y1*k)))
    g = np.asarray(cr.convert('L'),float)
    bg = np.asarray(cr.convert('L').filter(ImageFilter.MaxFilter(15)).filter(ImageFilter.GaussianBlur(20)),float)
    n = np.clip(g/np.maximum(bg,1)*255,0,255)
    bw = (n < 150).astype(np.uint8)*255
    Image.fromarray(255-bw).save(f'art_{name}.png')
    print(name, cr.size)
