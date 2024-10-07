import re
import datetime
from difflib import SequenceMatcher


"""
--------------------
MONTH HELPER METHODS AND DATA
--------------------
"""

months = {"jan" : "01", "feb" : "02", "mar" : "03", "apr" : "04", "may" : "05", "jun" : "06", 
          "jul" : "07", "aug" : "08" , "sep" : "09", "oct" : "10" , "nov" : "11", "dec" : "12"}

def convert_month(m):
    m = m.lower()
    if m in months:
        return months[m]
    else:
        return closest_month(m)
        

def closest_month(m):
    best_ratio = -1
    best = None
    for month in months:
        ratio = 0
        for i in range(0, 3):
            if(month[i] == m[i]):
                ratio += .333
        if ratio > best_ratio:
            best_ratio = ratio
            best = month
    if best_ratio > .5:
        return best
    else:
        return None
    

"""
--------------------
ANALYSIS OF DATE DATA BBOX
--------------------
"""


def clean_text_red(a):
    result = re.sub(' ','', a)
    result = re.sub('-','/', result)
    return result

#Analyize a list of bounding boxes to piece together dates
def analyze_data(results, date_regex, loose_regex, is_red):
    alt_best = None
    alt_box = None
    for (bbox, text, prob) in results:
        clean_text = clean_text_red(text)

        extract = re.match(date_regex, clean_text)
        if(extract is not None):
            date = extract.group().lower()
            if is_red:
                if(date[:3] not in months):
                    closest = closest_month(date[:3])
                    if closest is not None:
                        return closest + date[3:], bbox, None
                else:
                    return extract.group().lower(), bbox, None
            else:
                return extract.group().lower(), bbox, None
        second_best = re.match(loose_regex, clean_text)
        if(second_best is not None):
            alt_best = second_best.group().lower()
            alt_box = bbox
                    
    merged = merge_intervals(results)

    for (bbox, text, prob) in merged:
        clean_text = clean_text_red(text)
        extract = re.search(date_regex, clean_text)
        if(extract is not None):
            date = extract.group().lower()
            if is_red:
                if(date[:3] not in months):
                    closest = closest_month(date[:3])
                    if closest is not None:
                        return closest + date[3:], bbox, None
                else:
                    return extract.group().lower(), bbox, None
            else:
                return extract.group().lower(), bbox, None
        second_best = re.search(loose_regex, clean_text)
        if(second_best is not None):
            alt_best = second_best.group().lower()
            alt_box = bbox

    return "not found", alt_box, alt_best

#Helper method to merge different bbox in order to combine fractured text
def merge_intervals(results):    
    results = sorted(results, key=lambda x : x[0][0][0])
    for i in range(0, len(results)):
        bbox = results[i][0]
        (tl, tr, br, bl) = bbox

        for k in range(i + 1, len(results)):
            bbox_prev = results[k][0]
            (tl2, tr2, br2, bl2) = bbox_prev

            if(abs(tl2[0] - tr[0]) < 45 and abs(tl2[1] - tr[1]) < 45):
                new_string = results[i][1] + results[k][1]
                results[i] = (results[i][0], new_string, results[i][2])
                results[k] = ([tl, tr2, br2, bl], new_string, results[k][2])

    return results


"""
--------------------
DATE REGEX AND CHECKING
--------------------
"""

    #mm/dd/yyyy
type0 = r"(0?[1-9]|1[0,1,2])\/(0?[1-9]|[12][0-9]|3[01])\/(19|20)([0-2]?[0-9])"
    #mm/dd/yy
type1 = r"(0?[1-9]|1[0,1,2])\/(0?[1-9]|[12][0-9]|3[01])\/([0-2]?[0-9])"
    #yyyymmdd or yyyy-mm-dd
type2 = r"(19|20)\d{2}/?(0[1-9]|1[0,1,2])/?(0[1-9]|[12][0-9]|3[01])"
    #mmmddyyyy
type3 = r"([a-zA-Z]{3})/?(0?[1-9]|[12][0-9]|3[01])/?(19|20)[0-2][0-9]"
    #mmmddyy
type4 = r"([a-zA-Z]{3})/?(0?[1-9]|[12][0-9]|3[01])/?([0-2][0-9])"
    #YYYYmmmdd
type5 = r"((19|20)[0-2][0-9])/?([a-zA-Z]{3})/?(0?[1-9]|[12][0-9]|3[01])"
    #ddmmmyyyy
type6 = r"(0?[1-9]|[12][0-9]|3[01])/?([a-zA-Z]{3})/?((19|20)[0-2][0-9])"
    #ddmmmyy
type7 = r"(0?[1-9]|[12][0-9]|3[01])/?([a-zA-Z]{3})/?([0-2][0-9])"

regex = [re.compile(type0), re.compile(type1), re.compile(type2), re.compile(type3), re.compile(type4), re.compile(type5), re.compile(type6), re.compile(type7)]

def reformat_date(date):
    date = str(date)
    date = date.replace("-", "/")
    date = date.replace(" ", "")

    try:
        if(regex[0].match(date)):
            date_obj = datetime.datetime.strptime(date, "%m/%d/%Y")
            return date_obj.strftime("%Y%m%d")
        elif(regex[1].match(date)):
            date_obj = datetime.datetime.strptime(date, "%m/%d/%y")
            return date_obj.strftime("%Y%m%d")
        elif(regex[2].match(date)):
            date = date.replace("/", "")
            return date
        elif(regex[3].match(date)):
            date = date.replace("/", "")
            date_obj = datetime.datetime.strptime(date, "%b%d%Y")
            return date_obj.strftime("%Y%m%d")
        elif(regex[4].match(date)):
            date = date.replace("/", "")
            date_obj = datetime.datetime.strptime(date, "%b%d%y")
            return date_obj.strftime("%Y%m%d")
        elif(regex[5].match(date)):
            date = date.replace("/", "")
            date_obj = datetime.datetime.strptime(date, "%Y%b%d")
            return date_obj.strftime("%Y%m%d")
        elif(regex[6].match(date)):
            date = date.replace("/", "")
            date_obj = datetime.datetime.strptime(date, "%d%b%Y")
            return date_obj.strftime("%Y%m%d")
        elif(regex[7].match(date)):
            date = date.replace("/", "")
            date_obj = datetime.datetime.strptime(date, "%d%b%y")
            return date_obj.strftime("%Y%m%d")
        else:
            return "-1"
    except:
        faulty_index = -1
        try:
            for i in range(0, len(regex)):
                if regex[i].match(date):
                    faulty_index = i
                    break
        except:
            pass

        print("Date error: " + date + "  Faulty Regex: " + str(faulty_index))
        return "-1"