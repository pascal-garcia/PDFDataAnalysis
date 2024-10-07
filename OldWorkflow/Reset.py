import shutil
import os
import pandas as pd

result_path = r"Documents\Workflow\Result"
modified_folders_path = r'Documents\Workflow\mod_subfolder_storage.csv'
final_folders_path = r'Documents\Workflow\Final'


def reset():
    shutil.rmtree(result_path)
    os.mkdir(result_path)

def naming_reset():
    modified_folders = pd.read_csv(modified_folders_path, index_col=0)
    for i in range(0, modified_folders.size):
        folder = modified_folders.iloc[i].iloc[0]
        for file_name in os.listdir(folder):
            file_path = os.path.join(folder, file_name)
            os.remove(file_path)
    shutil.rmtree(final_folders_path)
    os.mkdir(final_folders_path)

naming_reset()
# reset()