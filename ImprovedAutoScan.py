import PathStorage
import os
import time
import shutil
import datetime
import pandas as pd

"""
Import the Conversion sheet - This is used primarily to skip folders that are deemed empty
"""

cleaner_data = pd.read_excel(PathStorage.conversion_sheet, index_col=0)


"""
Identify folders that ought to be skipped
"""
blacklist = []
for index, row in cleaner_data.iterrows():
    if(row.loc["EXCLUDE"] == "g"):
        blacklist.append(index)
        print("Blacklist: " + str(index))


"""
Count the number of files that were placed in the scan directory
"""
def count_scanned_files():
    current_count = 0
    for _ in os.listdir(PathStorage.scan_folder):
        current_count += 1
    return current_count

"""
move the files from the scan folder over to their specific result folder
"""
def transfer_scanned_files(to_folder):
    for file_name in os.listdir(PathStorage.scan_folder):
        print(file_name)
        file_path = os.path.join(PathStorage.scan_folder, file_name)
        copy_path = os.path.join(to_folder, file_name)
        shutil.copy2(file_path, copy_path)
        os.remove(file_path)


"""
Count number of folders that have already been generated 
"""
index = 1

folder_list = []
for folder in os.listdir(PathStorage.result_folder):
    folder_list.append(folder)
if(len(folder_list) > 0) :
    folder_list.sort()
    index = int(folder_list[len(folder_list) - 1].split(".")[0]) + 1

print("STARTING AT INDEX " + str(index) + "!")

while(index in blacklist):
    new_folder_path = os.path.join(PathStorage.result_folder, "{:03d}".format(index))
    os.mkdir(new_folder_path)
    print("Empty Folder created! #: " + "{:03d}".format(index))
    index += 1


"""Unitl the program terminates with a Ctrl-C, loop forever, attempting to detect files that were placed in the Scan folder"""
while(True):
    scan_count = count_scanned_files()
    if(scan_count == 0):
        time.sleep(5)
        print("beep!   " + str(datetime.datetime.now()))
    else:
        print("Found files!")
        time_count = 0
        prev_val = scan_count
        while(time_count < 10):
            num_files = count_scanned_files() 
            if(num_files != prev_val):
                prev_val = num_files 
                time_count = 0
            time_count += 1
            time.sleep(1)
        new_folder_path = os.path.join(PathStorage.result_folder, "{:03d}".format(index))
        os.mkdir(new_folder_path)
        transfer_scanned_files(new_folder_path)
        print("Folder created and transfered! #: " + "{:03d}".format(index))
        index += 1
        while(index in blacklist):
            new_folder_path = os.path.join(PathStorage.result_folder, "{:03d}".format(index))
            os.mkdir(new_folder_path)
            print("Empty Folder created! #: " + "{:03d}".format(index))
            index += 1
        time.sleep(3)