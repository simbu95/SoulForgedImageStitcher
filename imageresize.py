import PIL
import os
from PIL import Image, ImageOps
import glob
import shutil
import numpy as np

def resizeImages():
    jpgFilenamesList = glob.glob('*.jpg')
    if not os.path.exists('pngs'):
       os.makedirs('pngs')
    if not os.path.exists('jpgs'):
       os.makedirs('jpgs')

    for filename in jpgFilenamesList:
      baseImage = Image.open(filename)
      check = baseImage.convert('L')
      
      npim = np.array(check)
      print(filename)
      if(npim[192,100] >10  or npim[192,903] >10):
          print("250x250")
          png = baseImage.resize((250,250),PIL.Image.BICUBIC)
      elif(npim[196,100] >10  or npim[196,903] >10):
          print("500x500")
          png = baseImage.resize((500,500),PIL.Image.BICUBIC)
      elif(npim[198,99] >10 or npim[198,902] >10):
          print("750x750")
          png = baseImage.resize((750,750),PIL.Image.BICUBIC)
      else:
          print("1000x1000")
          png = baseImage
      mask = Image.open('Mask.png').convert('L')
      mask = ImageOps.fit(mask, png.size, centering=(0.5, 0.5))
      png.putalpha(mask.convert('1'))
      png.save('pngs/'+os.path.splitext(filename)[0] + '.png')
      shutil.move(filename, "jpgs/"+filename)

if __name__ == '__main__':
    resizeImages()
