import pymupdf
import PIL
from PIL import Image, ImageOps
import numpy as np
import PathStorage
import os
    
def split(array, start, end, left = 0, right = 1):
    start_pos = int(array.shape[0] * start)
    end_pos = int(array.shape[0] * end)
    left_pos = int(array.shape[1] * left)
    right_pos = int(array.shape[1] * right)
    return array[start_pos:end_pos,left_pos:right_pos,:]


png_index = 0

for folder in os.listdir(PathStorage.completed_path):
    folder_path = os.path.join(PathStorage.completed_path, folder)

    for file in os.listdir(folder_path):
        if file.split(".")[-1] == "pdf":
            pdf_path = os.path.join(folder_path, file)
            doc = pymupdf.open(pdf_path)
            page = doc.load_page(0)

            split_array = pdf_path.split("_")

            if split_array[4].split(".")[0] != "GC" and split_array[4].split(".")[0] != "Return Mail":
                subfolder = split_array[4].split(".")[0].split("-")[0]

            else:
                continue
            
            pix = page.get_pixmap(dpi=150)
            image = Image.frombytes("RGB", [pix.width, pix.height], pix.samples)
            array = np.asarray(image, dtype=np.int32)
            #sliced = split(array, .10, .55, 0, 1)
            sliced = split(array, .15, .4, .05, .9)

            img_path = os.path.join(PathStorage.pdf_normal_dataset, subfolder, "{:05d}".format(png_index) + "_" + file.split(".")[0] + ".png")

            im = Image.fromarray((sliced).astype(np.uint8))
            im.save(img_path)
                
            doc.close()

            png_index += 1
            if(png_index % 25 == 0):
                print(png_index)

          