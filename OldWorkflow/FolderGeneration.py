import pandas as pd
import os
import Reset
import re

cleaner_spreadsheet_path = r"C:\Users\PaGarcia\Documents\Workflow\Conversion.xlsx"
result_path = r"C:\Users\PaGarcia\Documents\Workflow\Result"
mod_subfolder_storage = r"C:\Users\PaGarcia\Documents\Workflow\mod_subfolder_storage.csv"
ori_subfolder_storage = r"C:\Users\PaGarcia\Documents\Workflow\ori_subfolder_storage.csv"


#Reset.reset()

cleaner_data = pd.read_excel(cleaner_spreadsheet_path)
cleaner_data.dropna(inplace=True)

file_names = []

for index, row in cleaner_data.iterrows():
    ending = "DS" if row["TYPE"] == "DROP STATION REGISTRATION" else "Fac"
    cutId = row["ID"][3:]
    file_names.append(f"{index + 1}-DCR_{cutId}_{ending}")

folder_path = []

for name in file_names:
    combined_path = os.path.join(result_path, name.strip())
    folder_path.append(combined_path)
    os.mkdir(combined_path)

pdf_variants = ['simplex', 'duplex', 'twopage']


ori_subfolder_paths = []
mod_subfolder_paths = []

for folder in folder_path:
    for variant in pdf_variants:
        sub_folder_path = os.path.join(folder, "ori_"+ variant)
        ori_subfolder_paths.append(sub_folder_path)
        os.mkdir(sub_folder_path)
    for variant in pdf_variants:
        sub_folder_path = os.path.join(folder, "mod_" + variant)
        mod_subfolder_paths.append(sub_folder_path)
        os.mkdir(sub_folder_path)

ori_subfolder_df = pd.DataFrame(ori_subfolder_paths)
ori_subfolder_df.to_csv(ori_subfolder_storage)

mod_subfolder_df = pd.DataFrame(mod_subfolder_paths)
mod_subfolder_df.to_csv(mod_subfolder_storage)