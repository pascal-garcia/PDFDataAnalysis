import re
from easyocr import Reader
import argparse
import cv2
import PathStorage
import os
import pdfHelper
import DateConversion
import time

temp_png_top = r"Documents\NewWorkflow\Temporary\topTemp.png"
temp_png_bottom = r"Documents\NewWorkflow\Temporary\bottomTemp.png"

def clean_text(a):
    return re.sub('[^0-9]','', a)

stamp_regex = r"2[0-9]{6}[0-9]$"
compiled_regex = re.compile(stamp_regex)

reader = Reader(["en"], False)

test_results = []
positives = 0
negatives = 0
false_positives = 0

index = 0

start = time.perf_counter()

for file in os.listdir(PathStorage.final_folder):
    combined = os.path.join(PathStorage.final_folder, file)
    correct = file.split("_")[3]
    pdfHelper.pdfpage_to_image(combined, temp_png_top, 0)
    array = pdfHelper.image_to_array(temp_png_top, 0, .1)
    array = pdfHelper.isolate_grey(array)
    pdfHelper.save_image_array(temp_png_top, array)
    image = cv2.imread(temp_png_top)
    results = reader.readtext(image, allowlist ='0123456789 ')
    found = None
    for r in results:
        result_name = clean_text(r[1])
        extract = re.search(DateConversion.regex3, result_name)
        if(extract is not None):
            found = extract.group()
            break
    if found is None:
        test_results.append("\n" + str(index) + "  n" + "  Correct: " + str(correct))
        negatives += 1
        print(str(index) + "  neg" + "  Correct: " + str(correct))
    elif found == correct:
        test_results.append("\n" + str(index) + "  p" + "  Correct: " + str(found))
        positives += 1
        print(str(index) + "  pos" + "  Correct: " + str(found))
    else :
        test_results.append("\n" + str(index) + "  fp Correct:  " + str(correct) + "  Incorrect: " + str(found))
        false_positives += 1
        print(str(index) + "  false pos" + "  Correct: " + str(correct) + "  Incorrect: " + str(found))
    
    index += 1

print(test_results)
print("pos: " + str(positives) + " neg: " + str(negatives) + "  false pos: " + str(false_positives))

print("TIME TAKEN: " + str(time.perf_counter() - start))