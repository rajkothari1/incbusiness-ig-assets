import glob, os
from PIL import Image
d = os.path.dirname(os.path.abspath(__file__))
files = sorted(f for f in glob.glob(os.path.join(d,'pages','[0-9]*.jpg')))
ims = [Image.open(f).convert('RGB') for f in files]
ims[0].save(os.path.join(d,'Halve_Hathe_Natvar_Kh_Shah.pdf'), save_all=True, append_images=ims[1:], resolution=200)
print(len(ims), 'pages')
