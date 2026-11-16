# Remove leftover starburst-border fragments (fractions of crop size)
from PIL import Image, ImageDraw
erase = {
 'dentist':  [(0.6,0,1,0.165)],
 'handstand':[(0,0,1,0.283),(0,0,0.09,0.45),(0.945,0,1,0.5),(0.955,0.78,1,0.92),(0.83,0.27,1,0.32),(0.935,0.38,1,0.43)],
 'cricketer':[(0,0,0.24,0.11),(0.86,0.39,1,0.57),(0,0.2,0.04,0.26),(0.92,0.37,1,0.42)],
}
for n,rects in erase.items():
    im = Image.open(f'art_{n}.png').convert('L'); w,h = im.size; d = ImageDraw.Draw(im)
    for x0,y0,x1,y1 in rects: d.rectangle((x0*w,y0*h,x1*w,y1*h), fill=255)
    im.save(f'art_{n}.png')
