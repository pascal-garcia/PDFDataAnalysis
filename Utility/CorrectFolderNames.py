import os
import PathStorage
import shutil

#shutil.rmtree(PathStorage.result_folder)


# for folder in os.listdir(PathStorage.result_folder):
#     old_path = os.path.join(PathStorage.result_folder, folder)
#     new_path = os.path.join(PathStorage.result_folder, "{:03d}".format(int(folder)))
#     os.rename(old_path, new_path)

# for folder in os.listdir(PathStorage.result_folder):
#     my_folder = os.path.join(PathStorage.result_folder, folder)
#     sum = 0
#     for file in os.listdir(my_folder):
#         sum += 1
#     for index, file in enumerate(os.listdir(my_folder)):
#         my_file = os.path.join(my_folder, file)
#         if(index > file)
#         os.remove(my_file)