import img2pdf
from PIL import Image, ImageOps
import os
import PIL
import pypdfium2 as pdfium
from PyPDF2 import PdfFileMerger, PdfFileReader, PdfWriter
import psutil
import numpy
import sys, pymupdf
import imageio.v2 as imageio
import numpy as np
import scipy.ndimage as nd

image_temp_path = r"Pictures\temp.png"
pdf_temp_path = r"Pictures\temp.pdf"
pdf_temp2_path = r"Pictures\temp2.pdf"

def pdfpage_to_image(pdf_path, img_path, image_page):
    doc = pymupdf.open(pdf_path)
    # Loop over pages and render
    page = doc.load_page(image_page)
    pix = page.get_pixmap(dpi=300)  # render page to an image
    pix.save(img_path)  # store image as a PNG
    doc.close()
    #pdf.close()

test_path = r"Pictures\Grey2.pdf"
pdfpage_to_image(test_path, "result.png", 1)

def image_to_pdf(img_path, pdf_path):
    with Image.open(img_path) as image:
 
        pdf_bytes = img2pdf.convert(image.filename)
 
        with open(pdf_path, "wb") as file:
            file.write(pdf_bytes)
            file.close()
    image.close()
   

def image_grayscale(in_path, out_path):
    with Image.open(in_path) as image:
        with ImageOps.grayscale(image) as image2:
            image2.save(out_path)
            image2.close()
    image.close()

def image_aggregates(image_path):
    with PIL.Image.open(image_path) as image:
        I = numpy.asarray(image)
        I = -1 * I
        return 0

def pdf_to_grayscale(in_path, out_path):
    # Load a document
    doc = pymupdf.open(pdf_path)
    pdf_length = len(doc)
    doc.close()
    #pdf.close()

    with PdfWriter() as writer:

        for i in range(0, pdf_length):
            print(i)
            print("Start Pdf to image")
            pdfpage_to_image(in_path, image_temp_path, i)
            print("Start image to greyscale")
            image_grayscale(image_temp_path, image_temp_path)
            print("Start greyscale to pdf")
            image_to_pdf(image_temp_path, pdf_temp_path)
            print("StartAppend")
            with open(pdf_temp_path, "rb") as input:
                writer.append(input)
                input.close()

        with open(out_path, "wb") as output:
            writer.write(output)
            print("Start write out")
            output.close()
        
        writer.close()

def image_to_array(path, start, end):
    image_array = imageio.imread(path)
    image_array = image_array.astype(np.int32)
    start_pos = int(image_array.shape[0] * start)
    end_pos = int(image_array.shape[0] * end)
    image_array = image_array[start_pos:end_pos,:,:]
    return image_array

def isolate_red_channel(new):
    new[:,:,0] -= new[:,:,1] + new[:,:,2]
    new[:,:,1] = 0
    new[:,:,2] = 0
    new = np.ceil(new)
    new[:,:,0] *= 100000
    new[:,:,1] = new[:,:, 0]
    new[:,:,2] = new[:,:, 0]
    new = np.clip(new, 0, 255)
    new = 255 - new
    new = new.astype(np.int32)
    return new

def isolate_grey(new):
    array = new
    array[array < 90] = 255
    array[array < 200] = 0
    array = nd.median_filter(array, 3)
    array[array < 220] = 0
    array = nd.maximum_filter(array, 3)
    array[array > 1] = 255
    array = nd.gaussian_filter(array, 3)
    array = nd.maximum_filter(array, 3)
    array[array < 200] = 0
    array[array > 1] = 255
    new = array.astype(np.int32)
    return new

def save_image_array(to_path, array):
    im = Image.fromarray((array).astype(np.uint8))
    im.save(to_path)


pdf_path = r"Pictures\Testing.pdf"
img_path = r"Pictures\output.png"
pdf_path2 = r"Pictures\pdfOut.pdf"

grey_path = r"Pictures\GreyscaleTest.pdf"
grey_path_out = r"Pictures\GreyscaleTestOut.pdf"

