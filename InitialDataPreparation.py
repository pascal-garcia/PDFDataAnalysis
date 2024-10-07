import PathStorage
import pandas as pd
import os
import pymupdf

"""
Import the sheet and initalize lists
"""
cleaner_data = pd.read_excel(PathStorage.conversion_sheet, index_col=0)
#cleaner_data.dropna(inplace=True)

blacklist = []

full_document_path = []

dcr_num_list = []
reg_type_list = []
folder_num_list = []
blank_list = []
page_count = []

folder_list = []    

"""
Helper function to count number of pages in a pdf
"""
def count_pages(pdf_path):
    doc = pymupdf.open(pdf_path)
    num_pages = 0
    for p in doc:
        num_pages += 1  
    doc.close()
    return num_pages


"""
SCRIPT:
Loop through all the documents that we scanned
Based on what folder they are in, we can connect them with their relevant folder specific information
"""

for folder_name in os.listdir(PathStorage.result_folder):
    folder_list.append(folder_name)

folder_list.sort()

folder_checklist = cleaner_data.index.to_list()
print(folder_checklist)

for index, folder in enumerate(folder_list):
    folder_num = float(folder)

    folder_checklist.remove(folder_num)

    skip = cleaner_data.loc[folder_num].loc["EXCLUDE"] == "g"

    if float(folder_num) != float(folder):
        raise Exception("Folder numbers are not consistent:  " + str(folder_num) + " " + str(folder))
    
    print("Consider: " + str(folder_num) + " " + folder)

    if folder_num in blacklist or skip:
        print("SKIP")
        continue

    
    folder_path = os.path.join(PathStorage.result_folder, folder)
    dcr_num =  cleaner_data.loc[folder_num].loc["CUTID"]
    fac_type = "Fac" if cleaner_data.loc[folder_num].loc["TYPE"] == "FACILITY REGISTRATION" else "DS"
    
    

    file_list = [x for x in os.listdir(folder_path)]
    file_list.sort()
    
    for file_index, file in enumerate(file_list):
        full_path = os.path.join(folder_path, file)
        num_pages = count_pages(full_path)
        #print(full_path)
        new_path = os.path.join(folder_path, "doc" + "_" + "{:03d}".format(file_index) + "_" + str(len(full_document_path)) + ".pdf")
        try:
            os.rename(full_path, new_path)
        except:
            pass
        full_document_path.append(new_path)
        dcr_num_list.append(dcr_num)
        reg_type_list.append(fac_type)
        folder_num_list.append(folder_num)
        blank_list.append(1 if num_pages == 1 else 0)
        page_count.append(num_pages)


"""
Prepare Final Information for final export to csv, which is the mechanism by which we will be storing the information on disk
"""


result_dict = { "Date" : dcr_num_list, "Action" : dcr_num_list, "Backpage" : dcr_num_list, "Blank" : blank_list, "DCR" : dcr_num_list, 
               "Type" : reg_type_list, "Folder": folder_num_list, "Path" : full_document_path, "Num Pages" : page_count}


print("Remaining: " + str(folder_checklist))

result = pd.DataFrame.from_dict(result_dict)

result["Date"] = ""
result["Action"] = 0
result["Backpage"] = 0
result["Detection"] = 0
result["DateType"] = 0
result["DateLocation"] = "e"
result["Destroy"] = 0

result.to_csv(PathStorage.docdata_sheet)





