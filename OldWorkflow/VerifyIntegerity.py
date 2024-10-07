import pandas as pd
import DateConversion

document_data_path = r'Documents\Workflow\document_data.xlsx'
document_data = pd.read_excel(document_data_path)

document_data = document_data.fillna("0")

threeCounter = 0
currentFolder = 1

for i in range(0, document_data.shape[0]):
    row = document_data.iloc[i]
    print(i)
    
    if len(str(row.loc["DATE"]).strip()) > 1:
        assert(DateConversion.reformat_date(str(row.loc["DATE"])) != "-1")

    if(row.loc["FOLDER"] != "0"):
        assert(int(row.loc["FOLDER"]) == currentFolder)

        threeCounter += 1
        if threeCounter == 3:
            threeCounter = 0
            currentFolder += 1
    
