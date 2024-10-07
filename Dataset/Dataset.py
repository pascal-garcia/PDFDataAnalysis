import pymupdf
import PIL
from PIL import Image, ImageOps
import numpy as np
import PathStorage
import os
    


png_index = 0

for folder in os.listdir(PathStorage.completed_path):
    folder_path = os.path.join(PathStorage.completed_path, folder)

    for file in os.listdir(folder_path):
        if file.split(".")[-1] == "pdf":
            pdf_path = os.path.join(folder_path, file)
            doc = pymupdf.open(pdf_path)

            for page_num, page in enumerate(doc):
                pix = page.get_pixmap(dpi=20)

                image = Image.frombytes("RGB", [pix.width, pix.height], pix.samples)


                subfolder = "Normal"
                split_array = pdf_path.split("_")

                if split_array[4].split(".")[0] == "GC" or split_array[4].split(".")[0] == "Return Mail":
                    subfolder = "GC"
                elif page_num > 0:
                    subfolder = "Backpage"
                
                img_path = os.path.join(PathStorage.pdf_dataset, subfolder, "{:05d}".format(png_index) + "_" + "{:02d}".format(page_num) + file.split(".")[0] + ".png")

                image.save(img_path)

            png_index += 1