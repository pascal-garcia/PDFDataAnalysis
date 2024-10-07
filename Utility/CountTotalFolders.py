import os
import PathStorage


png_index = 0

dcr_set = set()
count = 0

for folder in os.listdir(PathStorage.completed_path):
    folder_path = os.path.join(PathStorage.completed_path, folder)

    for file in os.listdir(folder_path):
        file_name_split = file.split("_")
        if(file_name_split[0] == "DCR"):
            dcr_set.add(file_name_split[1])
            count += 1


print(len(dcr_set))
print(count)