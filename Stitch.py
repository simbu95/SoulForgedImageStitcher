
###########################################################################
#To Do
###########################################################################

#Methods for different image offsets.

from PIL import Image
import numpy as np
import os
import shutil
import imageresize
import timeit
from numpy.lib.stride_tricks import as_strided

#Taken from https://stackoverflow.com/questions/17881489/faster-way-to-calculate-sum-of-squared-difference-between-an-image-m-n-and-a
def sumsqdiff3(input_image, template):
    window_size = template.shape
    y = as_strided(input_image,
                    shape=(input_image.shape[0] - window_size[0] + 1,
                           input_image.shape[1] - window_size[1] + 1,) +
                          window_size,
                    strides=input_image.strides * 2)
    ssd = np.einsum('ijkl,kl->ij', y, template)
    ssd *= - 2
    ssd += np.einsum('ijkl, ijkl->ij', y, y)
    ssd += np.einsum('ij, ij', template, template)

    return ssd

#Offset percentages and some global variables to handle restarts.
offsets = [(.5,.5, 50),(.17,.5, 75),(.83,.5, 75),(.5,.17, 75),(.5,.83, 75)]
offset = offsets[0]
ImagesAdded = 1
backups = 1
myoffset = 0

#If no png folder exists, create it and use imageresize to convert all jpgs in current file to pngs.
#Rename one of the pictures to base.png
if not os.path.exists('pngs'):
   imageresize.resizeImages()
   files = os.listdir("pngs")
   shutil.move('pngs/' + files[0], "pngs/base.png")

#Creating a couple more directories for storing images during/after the matching process.
if not os.path.exists('pngs/skip'):
   os.makedirs('pngs/skip')
if not os.path.exists('pngs/done'):
   os.makedirs('pngs/done')

#Keep looping until a stop condition
while True:
  #Find all the files in the pngs folder
  files = os.listdir("pngs")
  #if(not input("Is " + files[0] + " Correct?\n") == "y"):
  #    exit(0)
  
  #Check the first file, I assume all soulforged images are numbers, so they should come before base.png. If base.png is found, then use that to start a new loop.
  Filename = files[0]
  if(Filename == "base.png"):
    skipfiles = os.listdir("pngs/skip")
    #If there are files in the skip folder
    if skipfiles:
      #If there have been no images added to the base image
      #Increment the offset, or if all offsets used, exit.
      if(ImagesAdded == 0):
        if(myoffset < 4):
          myoffset = myoffset + 1
          print('Changing offsets to ' + str(myoffset))
          offset = offsets[myoffset]
        else:
          exit(0)
      #In any case, add all the skipped files back to the directory and try again.
      for f in skipfiles:
        src_path = os.path.join("pngs/skip", f)
        dst_path = os.path.join("pngs", f)
        shutil.move(src_path, dst_path)
        ImagesAdded = 0
      continue
    exit(0)
  
  print("Running Stitch " + Filename)
  ############################################
  #Open Both Images and convert to grayscale
  ############################################
  baseIM = Image.open('pngs/' + 'base.png')
  baseGray= baseIM.convert('L')
  addIM = Image.open('pngs/' + Filename)
  addGray = addIM.convert('L')
  
  #Get image sizes
  widthBase, heightBase = baseIM.size
  widthAdd, heightAdd = addIM.size
  
  #Make a crop of the image to add, which will be used for the scan
  size = offset[2]
  left = int(widthAdd*offset[0] - size/2)
  top = int(heightAdd*offset[1] - size/2)
  convIM = addGray.crop((left, top, left+size, top+size))
  
  #Convert images to numpy arrays
  npCanvas = np.array(baseGray, np.intc)
  npim = np.array(convIM, np.intc)
  
  #And calculate sum of squared differences (SSD)
  start_time = timeit.default_timer()
  convResult = sumsqdiff3(npCanvas, npim)
  elapsed = timeit.default_timer() - start_time
  print(elapsed)
  
  #Find out the location where the minimum difference in pixel color was found.
  loc = np.unravel_index(convResult.argmin(), convResult.shape)
  
  #Offset the location because of the new canvas size, and where the scanning image was versus where the boundary of the orignal image is. 
  diffx = loc[1] + widthAdd - left
  diffy = loc[0] + heightAdd - top
  
  #Prepare a new larger canvas to paste the image.
  new_width = widthBase + 2*widthAdd
  new_height = heightBase + 2*widthAdd
  
  Canvas = Image.new('RGBA', (new_width, new_height), (0,0,0,0))
  
  #Paste the background image, then past the foreground iamge with alpha.
  Canvas.paste(baseIM, (widthAdd, heightAdd))
  Canvas.paste(addIM, (diffx, diffy),addIM)
  
  imageBox = Canvas.getbbox()
  cropped = Canvas.crop(imageBox)
  
  #Check the result of the minimum SSD value... if above a threshold then fail the merge. (mine is set to 7 shades different on average, remember that SSD is squared difference)
  #The continue forces the loop onto the next image.
  print(convResult[loc[0],loc[1]])
  if(convResult[loc[0],loc[1]] > (7*7*size*size)):
      print("Error, very high sum, Skipping")
      #print(str(loc[1]) + "," + str(loc[0]))
      #convIM.show()
      cropped.save("ErrorCheck.png")
      shutil.move('pngs/' + Filename, "pngs/skip/"+Filename)
      #input("wait")
      continue
  ########################################################
  #If the threshold was passed, then save the image, and a backup, and move the added image to the done folder.
  shutil.move("pngs/base.png", "pngs/done/base.png")
  cropped.save("pngs/base.png")
  baseIM.save("backup" + str(backups) + ".png")
  backups = backups + 1
  shutil.move('pngs/' + Filename, "pngs/done/"+Filename)
  ImagesAdded = ImagesAdded + 1
  #If an offset was used, then change it back to regular centered search.
  if(myoffset != 0):
      myoffset = 0
      offset = offsets[0]
      print('Changing offsets to ' + str(myoffset))