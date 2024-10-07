
# import tkinter module
import tkinter as tk
import  PathStorage
import pandas as pd
import datetime
import numpy as np
import fitz
from PIL import Image, ImageTk
import pymupdf
import shutil
import DateConversion

"""
Import the CSV and initalize some formats
"""
doc_data = pd.read_csv(PathStorage.docdata_sheet, index_col=0)
try:
    doc_data["Date"] = doc_data["Date"].astype("Int64").astype("str")
    doc_data["Date"] = doc_data["Date"].replace("<NA>", "")
except:
    pass

doc_data.fillna("", inplace=True)


"""
Initialize some of the global variables
"""

doc_index = 0
digit_index = 0
date_toggle = False
next_doc_index = 1


#Workflow: FILTER: Create series of indexes of those only with what you want. Should be able to skip blanks and two pages and those without null dates

current_series = pd.DataFrame()
series_index = 0

date_length = 12

var_list = []

"""
Keyboard callback
Handles most all itneraction

37 - Left arrow
39 - right arrow
13 - Enter
189 -  minus
187 - enter/plus
46 - Delete
9 - Tab
8 - Backsapcce
192 - Squigly ~`
16 - Shift
"""

def onKeyPress(event):
    # print(event.keycode)
    global doc_index
    global series_index
    global digit_index
    global date_toggle
    global use_preloaded

    if(date_toggle):
        if(event.char.isalnum() or event.char == '-' or event.char == '/' or event.char == ' '):
            new_date = str(doc_data.loc[doc_index, "Date"])
            new_date = new_date[:digit_index] + event.char + new_date[digit_index + 1:]
            doc_data.loc[doc_index, "Date"] = new_date.strip() 
            digit_index = min(digit_index + 1, date_length - 1)
        elif(event.keycode == 13):
            date_toggle = False
        elif event.keycode == 37:
            #digit_index = max(digit_index - 1, 0)
            if(digit_index == 0):
                digit_index = (len(doc_data.loc[doc_index, "Date"]) - 1) % date_length
            else:
                digit_index = (digit_index - 1) % date_length
        elif event.keycode == 39:
            digit_index = min(digit_index + 1, date_length - 1)
        elif event.keycode == 8:
            digit_index = max(digit_index - 1, 0)
            new_date = str(doc_data.loc[doc_index, "Date"])
            new_date = new_date[:digit_index] + " " + new_date[digit_index + 1:]
            doc_data.loc[doc_index, "Date"] = new_date.strip() 
        elif event.keycode == 46:
            new_date = str(doc_data.loc[doc_index, "Date"])
            new_date = new_date[:digit_index] + " " + new_date[digit_index + 1:]
            doc_data.loc[doc_index, "Date"] = new_date.strip()
        elif event.keycode == 9:
            changeDocument(series_index + 1)
            use_preloaded = True
        elif event.keycode == 192:
            changeDocument(series_index - 1)
            
        updateValues(var_list)

        return
        
    if(False): #event.char.isdigit() or event.char == ' '
        new_date = str(doc_data.loc[doc_index, "Date"])
        new_date = new_date[:digit_index] + event.char + new_date[digit_index + 1:]
        doc_data.loc[doc_index, "Date"] = new_date 
        digit_index = min(digit_index + 1, 9)
    elif event.char in ('qwert') and event.char:
        doc_data.loc[doc_index, "Action"] = ('qwert'.index(event.char) + 1) % 5
    elif event.char == 'b':
        doc_data.loc[doc_index, "Blank"] = (int(doc_data.loc[doc_index, "Blank"]) + 1) % 2
    elif event.char == 'n':
        doc_data.loc[doc_index, "Backpage"] = (int(doc_data.loc[doc_index, "Backpage"]) + 1) % 2
    elif event.char == 'k':
        doc_data.loc[doc_index, "Destroy"] = (int(doc_data.loc[doc_index, "Destroy"]) + 1) % 2
    elif event.char == 's':
        saveSheet()
        return
    elif event.char == 'j':
        rotate(0)
    elif event.keycode == 189 or event.keycode == 192:
        changeDocument(series_index - 1)
    elif event.keycode == 187 or event.keycode == 9:
        use_preloaded = True
        changeDocument(series_index + 1)
    elif(event.keycode == 13):
        date_toggle = True
    
    updateValues(var_list)

"""
Rotates the current PDF
Unique, because this actuually changes the PDF file itself, and does not simply appply metadata to the document data sheet
"""

def rotate(page_num):
    doc_path = doc_data.loc[doc_index, "Path"]
    doc = pymupdf.open(doc_path)
    page = doc[page_num]
    page.set_rotation(page.rotation + 90)
    doc.saveIncr()
    doc.close()

    show_image(doc_data.loc[doc_index, "Path"], doc_data.loc[doc_index, "Date"], doc_data.loc[doc_index, "DateType"], doc_data.loc[doc_index, "DateLocation"])
    pass

"""
Mouse callback to prevent cursor from getting stuck in input boxes
"""
def change_focus(event):
    event.widget.focus_set()


"""
Handles scrolling through pdfs
Works to correlate the series and dox indexes
"""
def changeDocument(doc_num):
    global doc_index
    global digit_index
    global series_index
    global next_doc_index

    series_index = max(0, min(doc_num, current_series.shape[0] - 1))    
    doc_index = current_series.iloc[series_index, 0]

    next_series_index = max(0, min(doc_num + 1, current_series.shape[0] - 1))    
    next_doc_index = current_series.iloc[next_series_index, 0]

    digit_index = 0

prev_path = ""


"""
Convert the interger id of coding to a string
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
Updates the GUI to reflect changes to the doc_data sheet. 
"""
def updateValues(text_var_list):
    global date_toggle
    global prev_path
    global use_preloaded

    title_text.set("  " + str(doc_index) + " in folder " + str(doc_data.loc[doc_index, "Folder"]))
    folder_text.set("  |   " + str(series_index + 1) + "/" + str(current_series.shape[0]) + "  |  ")
    
    if(doc_data.loc[doc_index, "Blank"] == 0):
        text_var_list[2].set("No")
    else:
        text_var_list[2].set("Yes")

    if(doc_data.loc[doc_index, "Backpage"] == 0):
        text_var_list[3].set("No")
    else:
        text_var_list[3].set("Yes")
    
    if(doc_data.loc[doc_index, "Destroy"] == 0):
        text_var_list[4].set("No")
    else:
        text_var_list[4].set("Yes")

    text_var_list[0].set(int(doc_data.loc[doc_index, "DCR"]))
    text_var_list[1].set(doc_data.loc[doc_index, "Type"])


    text_var_list[6].set(valueToDocType(doc_data.loc[doc_index, "Action"], doc_data.loc[doc_index, "Type"]))

    fill_digits()

    for digit_label in digit_list:
        digit_label.config(bg=digit_label_color)
    digit_list[digit_index].config(bg="#337755")

    if(date_toggle):
        search_entry.config(state="disabled")
        date_mode_label.grid(column=6, row=len(var_list))
    else:
        search_entry.config(state="normal")
        date_mode_label.grid_forget()

    if(doc_data.loc[doc_index, "Path"] != prev_path):
        prev_path = doc_data.loc[doc_index, "Path"]
        show_image(doc_data.loc[doc_index, "Path"], doc_data.loc[doc_index, "Date"], doc_data.loc[doc_index, "DateType"], doc_data.loc[doc_index, "DateLocation"])
        preload_next(doc_data.loc[next_doc_index, "Path"])
    use_preloaded = False



"""
Updates the Date typing input bar specifically
"""
    
def fill_digits():
    read_in = str(doc_data.loc[doc_index, "Date"])
    for i, dl in enumerate(digit_list):
        if(i >= len(read_in) or read_in[i] == " "):
            dl.config(text="_")
        else:
            dl.config(text=read_in[i])
        
"""
Function to update the message box for easy output
"""

def show_msg(message_text, color):
    msg.config(text=message_text, bg=color)
    root.after(300, msg.config, {"bg": "#777777"})    


"""
Applies the changes from the dataframe to the csv
"""
def saveSheet():
    try:
        #shutil.copy2(PathStorage.docdata_sheet, PathStorage.docdata_backup_sheet)
        doc_data.to_csv(PathStorage.docdata_sheet)
        show_msg(message_text="last saved at " + str(datetime.datetime.now().strftime("on %m/%d/%Y at %I:%M %Ss")), color="#FFFFAA")
    except:
        show_msg(message_text="FAILED TO SAVE", color="#FF0000")

"""
Helper function to convert a pdf to an image
"""
def pdf_to_img(page_num, doc, mat):
    page = doc.load_page(page_num)
    pix = page.get_pixmap(matrix=mat)
    return Image.frombytes("RGB", [pix.width, pix.height], pix.samples)


"""
Some variables for preloading images for fast perforamnce
"""
prev_zoom_x = 0
prev_zoom_y = 0
preloaded_front = None
preloaded_back = None
preloaded_num_pages = 1
has_preloaded = False
use_preloaded = False

"""
This method handles the display of loading and display of pdf images 
"""

def show_image(pdf_path, date, date_type, date_loc):
    global blank_image
    global prev_zoom_x
    global prev_zoom_y
    global preloaded_front
    global preloaded_back
    global has_preloaded

    next_bar()
    doc = None

    preloaded_lock = has_preloaded and use_preloaded
    local_preloaded_front = preloaded_front
    local_preloaded_back = preloaded_back
    local_preloaded_num = preloaded_num_pages

    xoom = 1
    yoom = 1

    zoom_mult_x = root.winfo_screenwidth() / 1920
    zoom_mult_y = root.winfo_screenheight() / 1080

    if preloaded_lock:
        img_tk = local_preloaded_front
        num_pages = local_preloaded_num
        preloaded_front = None
        has_preloaded = False
    else:
        # open pdf file
        file_name = pdf_path
        doc = fitz.open(file_name)
        # transformation matrix we can apply on pages
        mat = fitz.Matrix(xoom * zoom_mult_x, yoom * zoom_mult_y)

        # count number of pages
        num_pages = 0
        for p in doc:
            num_pages += 1  

        im = pdf_to_img(0, doc, mat)
        img_tk = ImageTk.PhotoImage(im)

    
    date_font = ("Ariel", 20)

    if(date_loc != "e"):
        loc_list = date_loc.split(",")
        if len(loc_list) == 5:
            loc_list[1] = (loc_list[0] + loc_list[1])[:-1]
            loc_list = loc_list[1:]

        date_pad = (round(float(loc_list[0])) - 1000) // 17
        if date_type == 1 or date_type == 3 and not date[0].isdigit():
            date = date.upper()
            date_val = date[:3] + " " + date[3:5] + " " + date[5:]
        else: 
            date_val = date
        
        bounds = " " * abs(date_pad)
        if(date_pad > 0) :
            date_val = bounds + date_val 
        else:
            date_val = date_val + bounds

        if(date_type == 1):
            panel1.config(image=img_tk, compound="top", text=date_val, fg="#000000", font=date_font)
        elif(date_type == 2 or date_type == 3):
            panel1.config(image=img_tk, compound="bottom", text=date_val, fg="#000000", font=date_font)
    else:
        panel1.config(image=img_tk, compound="none", text="", fg="#000000")

    frame1.image = img_tk

    if(num_pages > 1):
        if preloaded_lock:
            img_tk = local_preloaded_back
            local_preloaded_back = None
        else:
            im = pdf_to_img(1, doc, mat)
            img_tk = ImageTk.PhotoImage(im)
        
        panel2.config(image=img_tk)
        frame2.image = img_tk
    else:
        if prev_zoom_x != zoom_mult_x or prev_zoom_y != zoom_mult_y:
            mat = fitz.Matrix(2.5 * zoom_mult_x * xoom, 2.27 * zoom_mult_y * yoom)
            im = pdf_to_img(0, blank_doc, mat)
            blank_image = ImageTk.PhotoImage(im)
        else:
            prev_zoom_x = zoom_mult_x
            prev_zoom_y = zoom_mult_y
        #blank_doc.close()
        panel2.config(image=blank_image)
        frame2.image = blank_image

    if doc is not None:
        doc.close()

"""
This handles preloading and caching the next pdf.
This is an optimzation technique to prevent buffering and slow loading when scrolling through pdfs
"""
def preload_next(pdf_path):
    global preloaded_front
    global preloaded_back
    global preloaded_num_pages
    global has_preloaded

    preloaded_front = None
    preloaded_back = None
    has_preloaded = False
    
    doc = None
    try:
        # open pdf file
        file_name = pdf_path
        doc = fitz.open(file_name)

        # transformation matrix we can apply on pages

        zoom_mult_x = root.winfo_screenwidth() / 1920
        zoom_mult_y = root.winfo_screenheight() / 1080

        xoom = 1
        yoom = 1
        mat = fitz.Matrix(xoom * zoom_mult_x, yoom * zoom_mult_y)

        # count number of pages
        num_pages = 0
        for p in doc:
            num_pages += 1  

        preloaded_num_pages = num_pages

        im = pdf_to_img(0, doc, mat)
        img_tk = ImageTk.PhotoImage(im)
        preloaded_front = img_tk

        if(num_pages > 1):
            im = pdf_to_img(1, doc, mat)
            preloaded_back = ImageTk.PhotoImage(im)

        has_preloaded = True
            
    finally:
        if doc is not None:
            doc.close()
    

"""
This handles the color flag system, which displays information relating to backpage merging
Red flag means document is the first document of a folder scanned, DO NOT MERGE WITH PREVIOUS
Green flag means previous document in filter series is the same as the global previous doucment, 
Green Flag means MAYBE merge. DO NOT MERGE if you don't have green flag unless you intentionally want to merge with non-GC documnet
"""
def next_bar():
    global doc_index
    global series_index

    next_index = max(0, min(series_index + -1, current_series.shape[0] - 1))    
    next_doc_index = current_series.iloc[next_index, 0]
    next_doc_folder = doc_data.loc[next_doc_index, "Folder"]
    
    is_subsequent = next_doc_index == doc_index + -1
    is_folder_start = doc_data.loc[max(0, doc_index - 1), "Folder"] != doc_data.loc[doc_index, "Folder"]
    
    file_bar.config(bg=background_dark)
    file_bar2.config(bg=background_dark)

    if(is_folder_start):
        file_bar.config(bg="#FF0000")
    if(is_subsequent):
        file_bar2.config(bg="#00FF00")

"""
This performs the critical filter functionality
It creates a sub series of documents from the global set off pdfs. 
"""
def filter():
    global current_series


    use_date = date_filter_var.get() != "Ignore"
    use_two = two_filter_var.get() != "Ignore"
    use_action = action_filter_var.get() != "Ignore"
    use_blank = blank_filter_var.get() != "Ignore"
    use_dateType = dateType_filter_var.get() != "Ignore"
    use_page = page_filter_var.get() != "Ignore"

    date_val = date_filter_var.get() == "Has Date"
    two_val = 0 if two_filter_var.get() == "Is Front Page" else 1
    action_val = -1 if not use_action else int(action_filter_var.get().split(":")[0])
    blank_val = -1 if not use_blank else int(blank_filter_var.get().split(":")[0])
    dateType_val = -1 if not use_dateType else int(dateType_filter_var.get().split(":")[0])
    page_val = -1 if not use_page else int(page_filter_var.get().split(":")[0])

    mask = ((date_val ^ (doc_data["Date"] == "")) | (not use_date)) & ((doc_data["Blank"] == blank_val) | (not use_blank)) & ((doc_data["Backpage"] == two_val) 
            | (not use_two)) & ((doc_data["Action"] == action_val) | (not use_action)) \
            & ((doc_data["DateType"] == dateType_val) | (not use_dateType)) & ((doc_data["Num Pages"] == page_val) | (not use_page))
                                                                    

    new_series = pd.DataFrame()
    new_series["DocIndex"] = doc_data.index[mask]

    if(new_series.shape[0] > 0):
        current_series = new_series
        changeDocument(0)
        updateValues(var_list)
        show_msg("FILTER SUCESS", "#00FF00")
    else:
        show_msg("ZERO DOCUMENTS!", "#FF0000")

"""
Handles the sereach functionality based on document number
"""
def search():
    term = search_var.get()
    try:
        term = int(term.strip())
    except:
        show_msg("NOT AN INT!", "#FF0000")
        return
    if term in current_series["DocIndex"].values:
        changeDocument(current_series.index[current_series["DocIndex"] == term].tolist()[0])
        updateValues(var_list)
        show_msg("FILTER SUCESS", "#00FF00")
    else:
        show_msg("NOT FOUND!", "#FF0000")

"""
Handles the search functionality for invalid dates
"""
def find_invalid_date():
    for index, val in current_series.iterrows():
        test_date = doc_data.loc[val.loc["DocIndex"], "Date"]
        if(DateConversion.reformat_date(test_date) == "-1"):
            changeDocument(index)
            updateValues(var_list)
            show_msg("FILTER SUCESS", "#00FF00")
            return
    show_msg("NOT FOUND!", "#FF0000")

"""
-----------------------
START OF THE TKINTER ELMENTS: This seciton is dedicated to actually declaring the UI elements and positioning them. We use Grid for layout  
------------------------
"""
# creating main tkinter window/toplevel
root = tk.Tk()
root.state('zoomed')



background_dark = "#111111"
root.config(background=background_dark)
#Blank, Backpage, DCR#, Date, 
label_font = ("Courier", 12, "bold")
value_font = ("Courier", 12)

#tk.Label(pad)

"""
Create elemetns for the right hand info column
"""

title_label = tk.Label(root, text = "Doc: ", fg = "#AA9955", font = ("System", 25, "bold"), pady = 20, anchor="e", bg = background_dark)
title_text = tk.StringVar(root, "_")
title_val = tk.Label(root, textvariable=title_text, fg = "#AA9955", font  = ("System", 25), pady = 20, anchor="w", bg = background_dark)

#title_label.grid(column=5, row=0)
title_val.grid(column=5, row=0)

folder_text = tk.StringVar(root, "_")
folder_val = tk.Label(root, textvariable=folder_text, fg = "#FF99BB", font  = ("System", 25), pady = 20, anchor="w", bg = background_dark)

folder_val.grid(column=6, row=0)

msg = tk.Message(root,text="Opened!", bg="#55FFFF", width=100)
msg.grid(row=0, column=8)

label_list = []
var_list = []

label_list.append(tk.Label(root, text = "DCR#:  "))
label_list.append(tk.Label(root, text = "Facility Type:  "))
label_list.append(tk.Label(root, text = "Is Blank?:  "))
label_list.append(tk.Label(root, text = "Is Backpage?:  "))
label_list.append(tk.Label(root, text = "Destroy?:  "))
label_list.append(tk.Label(root, text = "_________________"))
label_list.append(tk.Label(root, text = "Doc Type?:  "))
label_list.append(tk.Label(root, text = "Date?:  "))

for index, label in enumerate(label_list):
    label.config(width=18, anchor="e", font=label_font, fg = "#FFDDBB", bg = background_dark, pady=10)
    label.grid(column=5, row=index + 1)
    sv = tk.StringVar(root, value="_")
    value_insert = tk.Label(root, font=value_font, width = 18, anchor="w", fg= "#EEBBDD", bg = background_dark, pady=10, textvariable=sv)
    value_insert.grid(column=6, row=index + 1)
    var_list.append(sv)

digit_font = ("Arial", 12, "bold")
date_frame_color = "#111111"
date_frame = tk.Frame(root, bg=date_frame_color)
date_frame.grid(column=6, columnspan=date_length, row=len(var_list), rowspan=2, sticky="wn")
digit_list = []
digit_label_color = "#333333"
for i in range(0, date_length):
    digit_label = tk.Label(date_frame, bg=digit_label_color, width=1, font=digit_font, fg="#FFFFFF", padx=4, pady=4, text="_", anchor="w")
    digit_label.grid(column=i, row=0)
    digit_list.append(digit_label)

date_mode_label = tk.Label(root, font=value_font, width = 18, anchor="w", fg= "#EEBBDD", bg = background_dark, pady=2, text="DATE MODE")
date_mode_label.grid_forget()

button_frame = tk.Frame(root, bg=date_frame_color)
date_frame.grid(column=6, columnspan=6, row=len(var_list) + 1, rowspan=2, sticky="wn")

button_normal = tk.Button(root, text="Normal")

"""
Create the frames to hold the PDF images
"""

frame1 = tk.Frame(root)
panel1 = tk.Label(frame1, anchor="w")
panel1.grid(column=0, columnspan=1, row=0, rowspan=1)
frame1.grid(row=0, column=1, rowspan=12)


frame2 = tk.Frame(root)
panel2 = tk.Label(frame2)
panel2.grid(column=0, columnspan=3, row=0, rowspan=1)
frame2.grid(row=0, column=0, rowspan=12)

file_bar = tk.Frame(root, width=5, bg="#FF0000", height=400)
file_bar.grid(column=2, row=0, rowspan=6)
file_bar2 = tk.Frame(root, width=5, bg="#FF0000", height=400)
file_bar2.grid(column=2, row=6, rowspan=6)

barrier = tk.Label(root, text = "   ", bg=background_dark, pady=10, anchor="n")
barrier.grid(row=14, column=0)

filter_frame = tk.LabelFrame(root, bg="#222222", text="Filters", pady=20, font=("System", 24), fg="#FFFFFF")
filter_frame.grid(row=15, column=0, columnspan=2, rowspan=2, sticky="w")

"""
Create the area for the Filter and Search functionality
"""

dateLabel = tk.Label(filter_frame, text="Date Filter", font=label_font, padx=5)
dateLabel.grid(row=0, column=0)
options = ["Ignore", "Has Date", "No Date"]
date_filter_var = tk.StringVar(filter_frame)
date_filter_var.set("Ignore")
date_filter = tk.OptionMenu(filter_frame, date_filter_var, *options)    
date_filter.grid(row=1, column=0)

#0 - Not considered, 1 - Red Guessed, 2 - Grey Guessed, 3 - Red Partial, 4 - Grey Partial, 5 - Red Likely, 6 - Grey Likely
dateTypeLabel = tk.Label(filter_frame, text="Date Type", font=label_font, padx=5)
dateTypeLabel.grid(row=0, column=1)
options = ["Ignore", "0: Not Considered", "1: Red Guessed", "2: Grey Guessed", "3: Red Partial", "4: Grey Partial", "5: Red Likely", "6: Grey Likely"]
dateType_filter_var = tk.StringVar(filter_frame)
dateType_filter_var.set("Ignore")
dateType_filter = tk.OptionMenu(filter_frame, dateType_filter_var, *options)    
dateType_filter.grid(row=1, column=1)

twoPageLabel = tk.Label(filter_frame, text="TwoPage Filter", font=label_font, padx=5)
twoPageLabel.grid(row=0, column=2)
options = ["Ignore", "Is Back Page", "Is Front Page"]
two_filter_var = tk.StringVar(filter_frame)
two_filter_var.set("Ignore")
two_filter = tk.OptionMenu(filter_frame, two_filter_var, *options)    
two_filter.grid(row=1, column=2)

actionLabel = tk.Label(filter_frame, text="Action Filter", font=label_font, padx=5)
actionLabel.grid(row=0, column=3)
options = ["Ignore", "0: Renewal", "1: Intial", "2: Update", "3: Return Mail", "4: General Correspondence"]
action_filter_var = tk.StringVar(filter_frame)
action_filter_var.set("Ignore")
action_filter = tk.OptionMenu(filter_frame, action_filter_var, *options)    
action_filter.grid(row=1, column=3)

blankLabel = tk.Label(filter_frame, text="Blank Filter", font=label_font, padx=5)
blankLabel.grid(row=0, column=4)
options = ["Ignore", "0: No Blank Page", "1: Has Blank Page"]
blank_filter_var = tk.StringVar(filter_frame)
blank_filter_var.set("Ignore")
blank_filter = tk.OptionMenu(filter_frame, blank_filter_var, *options)    
blank_filter.grid(row=1, column=4)

page_label = tk.Label(filter_frame, text="Page Num Filter", font=label_font, padx=5)
page_label.grid(row=0, column=5)
options = ["Ignore", "1: Has One Page", "2: Has Two Pages"]
page_filter_var = tk.StringVar(filter_frame)
page_filter_var.set("Ignore")
page_filter = tk.OptionMenu(filter_frame, page_filter_var, *options)    
page_filter.grid(row=1, column=5)

apply_button = tk.Button(filter_frame, text="Apply", font=label_font, bg="#444444", fg="#44FF77", takefocus = 0, command=filter)
apply_button.grid(row=1, column=6)

search_frame = tk.LabelFrame(root, bg="#222222", text="Search", pady=20, font=("System", 24), fg="#FFFFFF")
search_frame.grid(row=15, column=6, columnspan=1, rowspan=2, sticky="w")

search_var = tk.StringVar(search_frame)
search_entry = tk.Entry(search_frame, textvariable=search_var, font=value_font, takefocus = 0)
search_entry.grid(row=0, column=0)

search_button = tk.Button(search_frame, text="Go!", font=label_font, bg="#444444", fg="#44FF77", takefocus = 0, command=search)
search_button.grid(row=1, column=0)

invalid_date_button = tk.Button(search_frame, text="Find Invalid date!", font=label_font, bg="#444444", fg="#44FF77", takefocus = 0, command=find_invalid_date)
invalid_date_button.grid(row=2, column=0)

blank_file = PathStorage.blank_page
blank_doc = fitz.open(blank_file)

# mat = fitz.Matrix(2.5, 2.27)
# im = pdf_to_img(0, blank_doc, mat)
# blank_image = ImageTk.PhotoImage(im)
# blank_doc.close()

"""
Initialize some values and start the GUI loop
"""

filter()
root.bind('<KeyPress>', onKeyPress)
root.bind_all('<Button>', change_focus)

# infinite loop which can be terminated by keyboard
# or mouse interrupt
tk.mainloop()
