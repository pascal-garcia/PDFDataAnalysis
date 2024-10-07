import re
import datetime


    #mm/dd/yyyy
type1 = r"(0?[1-9]|1[0,1,2])\/(0?[1-9]|[12][0-9]|3[01])\/(19|20)\d{2}"
    #mm/dd/yy
type2 = r"(0?[1-9]|1[0,1,2])\/(0?[1-9]|[12][0-9]|3[01])\/\d{2}"
    #yyyymmdd
type3 = r"(19|20)\d{2}(0[1-9]|1[0,1,2])(0[1-9]|[12][0-9]|3[01])"
    #mmm dd yyyy
type4 = r"([a-zA-Z]{3}) (0?[1-9]|[12][0-9]|3[01]) (19|20)\d{2}"

regex1 = re.compile(type1)
regex2 = re.compile(type2)
regex3 = re.compile(type3)
regex4 = re.compile(type4)

def convert_month(month):
    month = month.lower()
    match month:
        case "jan":
            return "01"
        case "feb":
            return "02"
        case "mar":
            return "03"
        case "apr":
            return "04"
        case "may":
            return "05"
        case "jun":
            return "06"
        case "jul":
            return "07"
        case "aug":
            return "08"
        case "sep":
            return "09"
        case "oct":
            return "10"
        case "nov":
            return "11"
        case "dec":
            return "12"
        case _:
            return "-1"

def reformat_date(date):
    date = date.replace("-", "/")
    
    if(regex1.match(date)):
        date_obj = datetime.datetime.strptime(date, "%m/%d/%Y")
        return date_obj.strftime("%Y%m%d")
    elif(regex2.match(date)):
        year_digits = date[len(date) - 2: len(date)]
        if(int(year_digits) > 50):
            year_digits = "19" + year_digits
        else:
            year_digits = "20" + year_digits

        date = date[:-2]
        date = date + year_digits
        date_obj = datetime.datetime.strptime(date, "%m/%d/%Y")
        return date_obj.strftime("%Y%m%d")
    elif(regex3.match(date)):
        return date
    elif(regex4.match(date)):
        month_val = convert_month(date[0:3])
        if(month_val == "-1"):
            return "-1"
        date_obj = datetime.datetime.strptime(month_val + date[3:], "%m %d %Y")
        return date_obj.strftime("%Y%m%d")
    else:
        return "-1"