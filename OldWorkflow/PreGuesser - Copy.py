import pandas as pd
import PathStorage
import re
from easyocr import Reader
import argparse
import cv2
import PathStorage
import os
import DateConversion
import time
from PIL import Image, ImageOps
import pymupdf
import numpy as np
import matplotlib.pyplot as plt
import imageio.v2 as imageio
import Testing.pdfHelper as ph
import scipy.ndimage as nd
import time

full_grey_date = r"((20)([0-1][0-9]|2[0-4]))(0[1-9]|1[0,1,2])(0[1-9]|[12][0-9]|3[01])"
full_red_date = r"([a-zA-Z]{3})(0[1-9]|[12][0-9]|3[01])((20)([0-1][0-9]|2[0-4]))"

loose_grey_date = r"2[0-9]{6,8}"
loose_red_date = r"([a-zA-Z]{2,4})[0-9]{5,7}"


#Threshold for if document is predicted to have a red stamp at the bottom, measured = 2209830.0
red_threshold = 1000000 

month_alpha = "janfebmrpyulgsoctvd0123456789 ".upper()
num_alpha = "0123456789 "

def split(array, start, end, left = 0, right = 1):
    start_pos = int(array.shape[0] * start)
    end_pos = int(array.shape[0] * end)
    left_pos = int(array.shape[1] * left)
    right_pos = int(array.shape[1] * right)
    return array[start_pos:end_pos,left_pos:right_pos,:]

def isolate_red(new):
    new = new.astype(np.float32)
    new[:,:,0] -= new[:,:,1] * .52
    new[:,:,0] -= new[:,:,2] * .52
    new[:,:,1] = 0
    new[:,:,2] = 0
    new[:,:,0] *= 100000
    new[:,:,0] = np.clip(new[:,:,0], 0, 255)
    new[:,:,1] = new[:,:, 0]
    new[:,:,2] = new[:,:, 0]
    new = nd.minimum_filter(new, 2)
    return new
    
def compute_red_sum(array):
    array = array.astype(np.float32)
    array[:,:,0] -= array[:,:,1] * .8
    array[:,:,0] -= array[:,:,2] * .8
    array[:,:,0] *= 100000
    array[:,:,0] = np.clip(array[:,:,0], 0, 255)
    return np.sum(array[:,:,0])

def isolate_grey(array):
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
    array = array.astype(np.int32)
    return array

def predict_on_slice(array, alphabet, filter_func, reader, regex, loose_regex, is_red):
    filtered = filter_func(array)
    im = Image.fromarray((filtered).astype(np.uint8))
    im.save(PathStorage.temp_png)
    cv2_version = cv2.imread(PathStorage.temp_png)
    results = reader.readtext(cv2_version, allowlist=alphabet)
    prediction, bbox, alt = DateConversion.analyze_data(results, regex, loose_regex, is_red)
    return prediction, bbox, alt

def predict(pdf_path, reader):
    # Open Document and convert into image array
    doc = pymupdf.open(pdf_path)
    page = doc.load_page(0)
    pix = page.get_pixmap(dpi=300)

    image = Image.frombytes("RGB", [pix.width, pix.height], pix.samples)
    array = np.asarray(image, dtype=np.int32)

    # Red Stamps:
    prediction, bbox, red_alt = predict_on_slice(np.copy(split(array, .85, 1)), month_alpha, isolate_red, reader, full_red_date, loose_red_date, True)

    if prediction != "not found":
        return prediction, 1, bbox, alt
    
    prediction, bbox, grey_alt = predict_on_slice(np.copy(split(array, .0, .15)), month_alpha, isolate_grey, reader, full_grey_date, loose_grey_date, False)

    if prediction != "not found":
        return prediction, 2, bbox, alt

    bottom_slice = split(array, .85, 1)

    red_sum = compute_red_sum(np.copy(bottom_slice))
    is_red = red_sum > red_threshold

    if(is_red):
        red_copy = red(np.copy(bottom_slice))
        im = Image.fromarray((red_copy).astype(np.uint8))
        alphabet = month_alpha
    else:
        top_slice = split(array, 0, .15)
        grey_copy = isolate_grey(np.copy(top_slice))
        im = Image.fromarray((grey_copy).astype(np.uint8))
        alphabet = num_alpha


    im.save(PathStorage.temp_png)
    cv2_version = cv2.imread(PathStorage.temp_png)

    
    results = reader.readtext(cv2_version, allowlist=alphabet)


    regex =  full_red_date if is_red else full_grey_date
    loose_regex = loose_red_date if is_red else loose_grey_date
    
    prediction, bbox, alt = DateConversion.analyze_data(results, regex, loose_regex, is_red)

    if(is_red):
        date_type = 1
    elif(prediction != "not found" or alt is not None):
        date_type = 2
    else:
        date_type = 0
    
    return prediction, date_type, bbox, alt





doc_data = pd.read_csv(PathStorage.docdata_sheet, index_col=0)
doc_data = doc_data.astype({"Date" : "object"})
temp = doc_data.fillna("")


start = time.perf_counter()

reader = Reader(["en"], False)

total, guessed, red_total, grey_total, black_total, red_guessed, grey_guessed, black_guessed, red_partial, grey_partial, black_partial = [0] * 11


result_string_list = []

start = 0
end = 10000

for index, data in doc_data.iterrows():
    if(index < start or index > end):
        continue
    if(doc_data.loc[index, "Backpage"] == 0 and doc_data.loc[index, "Action"] < 3):
        pdf_path = doc_data.loc[index, "Path"]
        guess, date_type, bbox, alt = predict(pdf_path, reader)

        print_line = guess + "   -   " + str(index)
        
        doc_data.loc[index, "DateType"] = date_type

        if(guess != "not found"):
            doc_data.loc[index, "Date"] = guess
            doc_data.loc[index, "DateLocation"] = str(bbox[0][0]) + "," + str(bbox[0][1])

            guessed += 1
            if(date_type == 1):
                red_guessed += 1
            elif(date_type == 2):
                grey_guessed += 1
            elif(date_type == 3):
                black_guessed += 1
        else:
            if(alt is not None):
                print_line += "   Close prediction: " + str(alt)
                if(date_type == 1):
                    red_partial += 1
                elif(date_type == 2):
                    grey_partial += 1
                elif(date_type == 3):
                    black_partial += 1

        print_line += "  -  " + str(date_type)
        
        print(print_line)
        result_string_list.append(print_line)

        total += 1
        if(date_type == 1):
            red_total += 1
        elif(date_type == 2 or date_type == 0):
            grey_total += 1
        elif(date_type == 3):
            black_total += 1


doc_data.to_csv(PathStorage.docdata_sheet)

total_ratio = "{:.2f}".format(guessed/total)
try:
    grey_ratio = "{:.2f}".format(grey_guessed/grey_total)
except:
    grey_ratio = "dbz"
try:
    red_ratio = "{:.2f}".format(red_guessed/red_total)
except:
    red_ratio = "dbz"
try:
    black_ratio = "{:.2f}".format(black_guessed/black_total)
except:
    black_ratio = "dbz"

l1 = "FINISHED WITH PROCESSING. TIME TAKEN:   " + str(time.perf_counter() - start)
l2 = "Total Ratio: " + total_ratio + "   Total#: " + str(total) + "   Guessed#: " + str(guessed)
l3 = "Grey Ratio: " + grey_ratio + "   Grey Total#: " + str(grey_total) + "   Grey Guessed#: " + str(grey_guessed) + "  Grey Partial#: " + str(grey_partial)
l4 = "Red Ratio: " + red_ratio + "   Red Total#: " + str(red_total) + "   Red Guessed#: " + str(red_guessed) + "  Red Partial#: " + str(red_partial)
l5 = "Black Ratio: " + black_ratio + "   Black Total#: " + str(black_total) + "   Black Guessed#: " + str(black_guessed) + "  Black Partial#: " + str(black_partial)

print(l1)
print(l2)
print(l3)
print(l4)
print(l5)

result_string_list.append(l1)
result_string_list.append(l2)
result_string_list.append(l3)
result_string_list.append(l4)
result_string_list.append(l5)

for index in range(0, len(result_string_list)):
    result_string_list[index] += "\n"

with open(PathStorage.output_txt, 'w') as s:
    s.seek(0)
    s.writelines(result_string_list)
    s.close()