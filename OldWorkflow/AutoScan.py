import pandas as pd
import shutil
import os

scan_path = r"Documents\Workflow\Scans"
subfolder_storage = r'Documents\Workflow\ori_subfolder_storage.csv'
index_file = r'Documents\Workflow\persistent_index.txt'
document_index_file = r'Documents\Workflow\document_index.txt'
document_data_path = r'Documents\Workflow\document_data.xlsx'

def increment_index(file):
    with open(file, 'r+') as s:
        value = int(s.read())
        value += 1
        s.seek(0)
        s.write(str(value))
        s.close()

def get_index(file):
    with open(file, 'r') as s:
        value = int(s.read())
        s.close()
        return value
        

all_subfolders = pd.read_csv(subfolder_storage, index_col=0)
index = get_index(index_file)
subfolder_path = all_subfolders.iloc[index].iloc[0]
print(subfolder_path)
for file_name in os.listdir(scan_path):
    print(file_name)
    file_path = os.path.join(scan_path, file_name)
    copy_path = os.path.join(subfolder_path, file_name)
    shutil.copy2(file_path, copy_path)
    os.remove(file_path)
    increment_index(document_index_file)

excel_doc_index = get_index(document_index_file)
document_data = pd.read_excel(document_data_path)
cur_row = document_data.iloc[excel_doc_index].loc["DATE"]
print("INDEX: " + str(excel_doc_index) + "  CurrentDocDate(Should be q): " + str(cur_row))

increment_index(document_index_file)
increment_index(index_file)