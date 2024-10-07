import os
import pandas as pd
import DateConversion
import shutil

original_folders_path = r'Documents\Workflow\ori_subfolder_storage.csv'
modified_folders_path = r'Documents\Workflow\mod_subfolder_storage.csv'
document_data_path = r'Documents\Workflow\document_data.xlsx'
final_folders_path = r'Documents\Workflow\Final'


    
def extract_path_details(path):
    end = path.rfind("\\")
    start = 44

    path = path[start:end]
    dcr_start = path.find("DCR")
    dcr_end = path.rfind("_")
    dcr = path[dcr_start: dcr_end]
    location_type = path[dcr_end:]
    location_type = location_type.replace("_","-")
    return (dcr, location_type)

def create_new_name(dcr, location_type, date, action):
    if(action == 1):
        end = "Initial" + location_type
    if(action == 0):
        end = "Renewal" + location_type
    if(action == 2):
        end = "Update" + location_type
    if(action == 3):
        end = "Return Mail"
    if(action == 4):
        end = "GC"
    return dcr + "_RE_" + date + "_" + end + ".pdf"

original_folders = pd.read_csv(original_folders_path, index_col=0)
modified_folders = pd.read_csv(modified_folders_path, index_col=0)

document_data = pd.read_excel(document_data_path)
document_data["TYPE"] = document_data["TYPE"].fillna(0)
document_data["SUS"] = document_data["SUS"].fillna("F")

doc_index = 0

for i in range(0, original_folders.size):
    orig = original_folders.iloc[i].iloc[0]
    mod = modified_folders.iloc[i].iloc[0]

    path_det = extract_path_details(orig)

    ordered_files = []
    for file_name in os.listdir(orig):
        ordered_files.append(file_name)
    ordered_files.sort()

    for file_name in ordered_files:
        orig_file_path = os.path.join(orig, file_name)
        doc = document_data.iloc[doc_index]
        formatted_date = DateConversion.reformat_date(str(doc["DATE"]))
        if(formatted_date == "-1"):
            raise Exception("INVALID DATE: " + str(doc["DATE"]) + "_ _index: " + str(doc_index))
        new_name  = create_new_name(path_det[0], path_det[1], formatted_date, doc["TYPE"])
        mod_file_path = os.path.join(mod, new_name)
        final_file_path = os.path.join(final_folders_path, new_name)
        shutil.copy2(orig_file_path, mod_file_path)
        shutil.copy2(orig_file_path, final_file_path)
        doc_index += 1
    if(len(str(document_data.iloc[doc_index].loc["DATE"]).strip()) > 1 != 1):
        raise Exception("Found date instead of q break at: " + str(doc["DATE"]) + ":  index: " + str(doc_index) + ": excel pos: " + str(doc_index + 2))
    doc_index += 1







    

