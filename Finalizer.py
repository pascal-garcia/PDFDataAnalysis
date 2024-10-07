import PathStorage
import pandas as pd
import pymupdf
import DateConversion
import shutil
import os

"""
Converts the integer id of the coding into the string value
"""
def valueToDocType(val, fac_type):
    match val:
        case 0:
            return "Renewal-" + fac_type
        case 1:
            return "Initial-" + fac_type
        case 2:
            return "Update-" + fac_type
        case 3:
            return "Return Mail"
        case 4:
            return "GC"
        
"""
SCRIPT
"""

doc_data = pd.read_csv(PathStorage.docdata_sheet, index_col=0)

#Dropped

dropped = doc_data.drop(doc_data[doc_data["Backpage"] == 1].index)
dropped["Date"] = dropped["Date"].map(DateConversion.reformat_date)
doc_data["Date"] = dropped["Date"]
failed_dates = dropped.loc[dropped["Date"] == "-1"]

if(failed_dates.shape[0] > 1):
    raise Exception("Failed dates: " + str(failed_dates))


form_mask = (dropped["Action"] == 4) | (dropped["Action"] == 3)
dropped = dropped.drop(dropped[form_mask].index)
dropped = dropped.sort_values("Date").drop_duplicates(['DCR'])

doc_data.loc[dropped.index, "Action"] = 1

"""
CREATE COPIES OF PDF FOR THE FINAL RESULT
APPLY CHANGES TO PDF, INCLUDING MERGING AND PAGE DELETION
"""

prev_path = None

shutil.rmtree(PathStorage.labeled_path)
os.mkdir(PathStorage.labeled_path)

for index, row in doc_data.iterrows():
    if(row["Destroy"] == 1):
        continue
    
    orig_path = row["Path"]
    new_path = os.path.join(PathStorage.labeled_path, "{:04d}".format(index) + ".pdf")

    if(row["Blank"] != 1 and row["Backpage"] != 1):
        prev_path = new_path
        shutil.copy2(orig_path, new_path)
        continue

    doc = pymupdf.open(orig_path)

    if(row["Blank"] == 1):
        try:
            doc.delete_page(1)
        except:
            pass
    
    if(row["Backpage"] == 1):
        full_doc = pymupdf.open(prev_path)
        full_doc.insert_pdf(doc)
        full_doc.saveIncr()
        full_doc.close()
    else:
        doc.save(new_path)
        prev_path = new_path
    
    doc.close()
 
    
"""
ACTUALLY RENAME THE FILES CORRECTLY
"""
for file in os.listdir(PathStorage.labeled_path):
    index = int(file.split(".")[0])
    row = doc_data.loc[index]
    orig_path = os.path.join(PathStorage.labeled_path, file)
    formatted_date = DateConversion.reformat_date(str(row["Date"]))
    if(formatted_date == "-1"):
        print("INVALID DATE: " + str(row["Date"]) + "--  ORIG PATH:  " + orig_path + "--  INDEX:  " + str(index))
        continue
    
    name = "DCR_" + str(int(row["DCR"])) + "_RE_" + formatted_date + "_" + valueToDocType(row["Action"], str(row["Type"]))
    final_file_path = os.path.join(PathStorage.labeled_path, name + ".pdf")
    try:
        os.rename(orig_path, final_file_path)
    except:
        doc = pymupdf.open(orig_path)
        full_doc = pymupdf.open(final_file_path)
        full_doc.insert_pdf(doc)
        full_doc.saveIncr()
        full_doc.close()
        doc.close()
        os.remove(orig_path)
        print("WARNING: FILE HAD SAME NAME AS OTHER, WAS MERGED. --FILE NAME: " + name + "--  ORIG PATH:  " + orig_path + "--  INDEX:  " + str(index))
