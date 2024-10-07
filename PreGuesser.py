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

"""
---------------
CONSTANTS
---------------
"""

full_grey_date = r"((20)([0-1][0-9]|2[0-4]))(0[1-9]|1[0,1,2])(0[1-9]|[12][0-9]|3[01])"
full_red_date = r"([a-zA-Z]{3})(0[1-9]|[12][0-9]|3[01])((20)([0-1][0-9]|2[0-4]))"

loose_grey_date = r"2[0-9]{6,8}"
loose_red_date = r"([a-zA-Z]{2,4})[0-9]{5,7}"


#Threshold for if document is predicted to have a red stamp at the bottom, measured = 2209830.0
red_threshold = 1000000 

month_alpha = "janfebmrpyulgsoctvd0123456789 ".upper()
num_alpha = "0123456789 "


"""
---------------
IMAGE PROCESSING
---------------
"""

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

"""
---------------
PREDICTION
---------------
"""

def predict_on_slice(array, alphabet, filter_func, reader, regex, loose_regex, is_red):
    filtered = filter_func(array)
    im = Image.fromarray((filtered).astype(np.uint8))
    im.save(PathStorage.temp_png)
    cv2_version = cv2.imread(PathStorage.temp_png)
    results = reader.readtext(cv2_version, allowlist=alphabet)
    prediction, bbox, alt = DateConversion.analyze_data(results, regex, loose_regex, is_red)
    return prediction, bbox, alt

"""
Date Types:
0: not guessed
1: red found
2: grey found
3: red partial
4: grey partial
5: likely red
6: likely not red
"""

def predict(pdf_path, reader):
    # Open Document and convert into image array
    doc = pymupdf.open(pdf_path)
    page = doc.load_page(0)
    pix = page.get_pixmap(dpi=300)
    doc.close()

    image = Image.frombytes("RGB", [pix.width, pix.height], pix.samples)
    array = np.asarray(image, dtype=np.int32)

    bottom_slice = split(array, .85, 1)

    red_sum = compute_red_sum(np.copy(bottom_slice))
    is_red = red_sum > red_threshold

    if is_red:
    # Red Stamps:
        prediction, bbox, red_alt = predict_on_slice(np.copy(split(array, .85, 1)), month_alpha, isolate_red, reader, full_red_date, loose_red_date, True)
        if prediction != "not found":
            return prediction, 1, bbox, None
        
        prediction, bbox, grey_alt = predict_on_slice(np.copy(split(array, .0, .15)), month_alpha, isolate_grey, reader, full_grey_date, loose_grey_date, False)
        if prediction != "not found":
            return prediction, 2, bbox, None
    else:
        prediction, bbox, grey_alt = predict_on_slice(np.copy(split(array, .0, .15)), month_alpha, isolate_grey, reader, full_grey_date, loose_grey_date, False)
        if prediction != "not found":
            return prediction, 2, bbox, None
    
        prediction, bbox, red_alt = predict_on_slice(np.copy(split(array, .85, 1)), month_alpha, isolate_red, reader, full_red_date, loose_red_date, True)
        if prediction != "not found":
            return prediction, 1, bbox, None    
        

    if red_alt is not None and grey_alt is not None:
        return "not found", 3, bbox, red_alt
    elif red_alt is None and grey_alt is not None:
        return "not found", 4, bbox, grey_alt
    elif grey_alt is None and red_alt is not None:
        return "not found", 3, bbox, red_alt
    

    if is_red:
        return "not found", 5, None, None
    else:
        return "not found", 6, None, None



"""
---------------
MAIN SCRIPT/FILE LOOP
---------------
"""



doc_data = pd.read_csv(PathStorage.docdata_sheet, index_col=0)
doc_data = doc_data.astype({"Date" : "object"})
temp = doc_data.fillna("")


start_time = time.perf_counter()

reader = Reader(["en"], False)

total, guessed, red_total, grey_total, red_guessed, grey_guessed, red_partial, grey_partial, red_likely, grey_likely = [0] * 10

prev_date = "2018"

result_string_list = []

start = 0
end = 12000

for index, data in doc_data.iterrows():
    if(index < start or index > end):
        continue
    if(doc_data.loc[index, "Backpage"] == 0 and doc_data.loc[index, "Action"] < 3):
        pdf_path = doc_data.loc[index, "Path"]
        guess, date_type, bbox, alt = predict(pdf_path, reader)

        
        doc_data.loc[index, "DateType"] = date_type
        
        #Decided not to use BBC for alt guesses, 
        # if bbox is not None:
        #     doc_data.loc[index, "DateLocation"] = str(bbox[0][0]) + "," + str(bbox[0][1]) + "," + str(bbox[2][0]) + "," + str(bbox[2][1])

        try:
            if index > 1 and doc_data.loc[index, "Folder"] != doc_data.loc[index - 1, "Folder"]:
                prev_date = "2018"

            if(date_type == 2):
                if prev_date is not None:
                    if int(prev_date[:4]) >= 2018 and int(guess[:4]) == 2010:
                        guess = "2018" + guess[4:]
                    elif int(prev_date[:4]) < 2015 and int(guess[:4]) == 2018:
                        guess = "2010" + guess[4:]
                
            if(date_type < 3):
                prev_date = guess
        except:
            #print("Fail Change")
            pass

        print_line = guess + "   -   " + str(index)

        if(guess != "not found"):
            doc_data.loc[index, "Date"] = guess
            doc_data.loc[index, "DateLocation"] = str(bbox[0][0]) + "," + str(bbox[0][1]) + "," + str(bbox[2][0]) + "," + str(bbox[2][1])
            guessed += 1
        elif(alt is not None):
            print_line += "   Close prediction: " + str(alt)        

        print_line += "  -  " + str(date_type)
        print(print_line)
        result_string_list.append(print_line)

        total += 1
        match(date_type):
            case 1:
                red_guessed += 1
            case 2:
                grey_guessed += 1
            case 3:
                red_partial += 1
            case 4:
                grey_partial += 1
            case 5:
                red_likely += 1
            case 6:
                grey_likely += 1

        if(date_type % 2 == 1):
            red_total += 1
        else:
            grey_total += 1



doc_data.to_csv(PathStorage.docdata_sheet)


"""
---------------
STATISTICS AND METADATA
---------------
"""

total_ratio = "{:.2f}".format(guessed/total)
try:
    grey_ratio = "{:.2f}".format(grey_guessed/grey_total)
except:
    grey_ratio = "dbz"
try:
    red_ratio = "{:.2f}".format(red_guessed/red_total)
except:
    red_ratio = "dbz"


l1 = "FINISHED WITH PROCESSING. TIME TAKEN:   " + str(time.perf_counter() - start_time)
l2 = "Total Ratio: " + total_ratio + "   Total#: " + str(total) + "   Guessed#: " + str(guessed)
l3 = "Grey Ratio: " + grey_ratio + "   Grey Total#: " + str(grey_total) + "   Grey Guessed#: " + str(grey_guessed) + "  Grey Partial#: " + str(grey_partial) + "  Grey Likely#: " + str(grey_likely)
l4 = "Red Ratio: " + red_ratio + "   Red Total#: " + str(red_total) + "   Red Guessed#: " + str(red_guessed) + "  Red Partial#: " + str(red_partial) + "  Red Likely#: " + str(red_likely)

print(l1)
print(l2)
print(l3)
print(l4)

result_string_list.append(l1)
result_string_list.append(l2)
result_string_list.append(l3)
result_string_list.append(l4)

for index in range(0, len(result_string_list)):
    result_string_list[index] += "\n"

with open(PathStorage.output_txt, 'w') as s:
    s.seek(0)
    s.writelines(result_string_list)
    s.close()