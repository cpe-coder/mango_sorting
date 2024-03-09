import numpy as np
import cv2

def get_limits(color):

   ripe_color_range = ([255, 191, 0],
                    [255, 234, 0],
                    [253, 218, 13],
                    [255, 255, 143],
                    [255, 215, 0],
                    [255, 192, 0],
                    [252, 245, 95],
                    [218, 165, 32],
                    [250, 250, 51],
                    [255, 255, 0],
                    )  
   raw_color_range = ([80, 200, 120],
                   [34, 139, 34],
                   [124, 252, 0],
                   [0, 128, 0],
                   [76, 187, 23],
                   [50, 205, 50],
                   [11, 218, 81],
                   [15, 255, 80],
                   ) 
   
   if color == [255, 255, 0]:
      return np.array(ripe_color_range[0], dtype=np.uint8), np.array(ripe_color_range[1], dtype=np.uint8)
   elif color == [0, 128, 0]: 
      return np.array(raw_color_range[0], dtype=np.uint8), np.array(raw_color_range[1], dtype=np.uint8)
   else:
      raise ValueError("Unsupported color")
