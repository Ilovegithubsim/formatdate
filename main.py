from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
from datetime import datetime, timedelta
import re

app = FastAPI()

# Helper functions (translated from JavaScript to Python)
def preprocess_input(input_str):
    extraneous_words = ["ค่ะ", "ละกัน", "อืม", "นะ", "คะ", "จ้ะ", "จ้า", "ค่า", "คับ"]
    thai_day_abbreviations = {'ครับ': ''}
    
    def ignore_words(input_str):
        pattern = re.compile(r'^(เช็คอินเป็นวันที่|เช็คเอ้าท์เป็นวันที่|ขอเช็คอินวันที่|ขอเช็คเอ้าท์วันที่|เข้าพักวันที่|ออกวันที่|ขอเข้าพักวันที่|ขอเข้าพักเป็นวันที่|ขอเข้าพัก|เช็คอิน|เช็คเอ้าท์|เข้าวันที่|เข้า|ออก|จองวันเข้า|จองวันออก|เอาเป็นวันที่|ขอเข้าวันที่|ขอออกวันที่|อยากเช็คอินวันที่|อยากเข้าพักวันที่|อยากเช็คอิน|อยากเช็คเอ้าท์|อยากเช็คเอ้าท์วันที่|อยากพักวันที่|อยากเอาวันที่|อยากได้เป็นวันที่|อยากเช็คอินในวันที่|อยากเช็คเอ้าท์ในวันที่|จะเช็คอินวันที่|จะเช็คเอ้าท์วันที่|จะเข้าวันที่|จะออกวันที่|จะขอเข้าวันที่|จะขอออกวันที่|จะเข้าไปวันที่|จะพักวันที่|จะเข้าพักวันที่|จะไปเช็คอินวันที่|จะไปเช็คอิน|จะเช็คเอ้าท์วันที่|จะเช็คอิน|จะเช็คเอ้าท์|น่าจะวันที่|น่าจะเป็นวันที่|น่าจะเข้าวันที่|น่าจะ|น่าจะออกวันที่|น่าจะเข้า|คิดว่าวันที่|Check In เป็นวันที่|Check Out เป็นวันที่|ขอ Check In วันที่|ขอ Check Out วันที่|อยาก Check In วันที่|อยาก Check Out วันที่|อยาก Check In|อยาก Check Out|อยาก Check Out วันที่|อยาก Check In ในวันที่|อยาก Check Out ในวันที่|จะ Check In วันที่|จะ Check Out วันที่|จะ Check In|จะ Check Out|จะไป Check In วันที่|จะไป Check In|อยากได้วันที่|)|ครับผม|ได้ไหมคะ|ได้ไหมครับ|ได้ไหม|$', re.IGNORECASE)
        return re.sub(pattern, ' ', input_str)

    cleaned_input = input_str.strip()
    for word in extraneous_words:
        regex = re.compile(r'\b' + word + r'\b', re.IGNORECASE)
        cleaned_input = regex.sub('', cleaned_input)

    for abbr, full in thai_day_abbreviations.items():
        regex = re.compile(r'\b' + abbr + r'\b', re.IGNORECASE)
        cleaned_input = regex.sub(full, cleaned_input)

    cleaned_input = ignore_words(cleaned_input)
    cleaned_input = re.sub(r'\s+', ' ', cleaned_input).strip()
    
    return cleaned_input

def format_date(date):
    if not date or not isinstance(date, datetime):
        return "Invalid date"
    
    thai_month_names = [
        'มกราคม', 'กุมภาพันธ์', 'มีนาคม', 'เมษายน',
        'พฤษภาคม', 'มิถุนายน', 'กรกฎาคม', 'สิงหาคม',
        'กันยายน', 'ตุลาคม', 'พฤศจิกายน', 'ธันวาคม'
    ]
    
    day = date.day
    month = thai_month_names[date.month - 1]
    return f"{day} {month}"

def parse_duration(duration_or_checkout):
    duration_or_checkout = duration_or_checkout.lower().strip()
    
    day_regex = re.compile(r'(\d+)\s*วัน')
    night_regex = re.compile(r'(\d+)\s*คืน')
    week_regex = re.compile(r'(\d+)\s*(สัปดาห์|อาทิตย์)')
    month_regex = re.compile(r'(\d+)\s*เดือน')
    year_regex = re.compile(r'(\d+)\s*ปี')
    
    night_match = night_regex.match(duration_or_checkout)
    if night_match:
        return int(night_match.group(1))
    
    day_match = day_regex.match(duration_or_checkout)
    if day_match:
        return int(day_match.group(1))
    
    week_match = week_regex.match(duration_or_checkout)
    if week_match:
        return int(week_match.group(1)) * 7
    
    month_match = month_regex.match(duration_or_checkout)
    if month_match:
        return int(month_match.group(1)) * 30
    
    year_match = year_regex.match(duration_or_checkout)
    if year_match:
        return int(year_match.group(1)) * 365
    
    if duration_or_checkout == "หนึ่งสัปดาห์":
        return 7
    
    return None

def parse_relative_date(input_str, reference_date=None):
    if reference_date is None:
        reference_date = datetime.now()
    
    thai_months = {
        'มกราคม': 0, 'กุมภาพันธ์': 1, 'มีนาคม': 2, 'เมษายน': 3,
        'พฤษภาคม': 4, 'มิถุนายน': 5, 'กรกฎาคม': 6, 'สิงหาคม': 7,
        'กันยายน': 8, 'ตุลาคม': 9, 'พฤศจิกายน': 10, 'ธันวาคม': 11,
        'มกรา': 0, 'กุมภา': 1, 'มีนา': 2, 'เมษา': 3,
        'พฤษภา': 4, 'มิถุนา': 5, 'กรกฎา': 6, 'สิงหา': 7,
        'กันยา': 8, 'ตุลา': 9, 'พฤศจิกา': 10, 'ธันวา': 11
    }

    relative_dates = {
        'วันนี้': lambda: reference_date,
        'พรุ่งนี้': lambda: reference_date + timedelta(days=1),
        'วันพรุ่งนี้': lambda: reference_date + timedelta(days=1)
    }
    
    if input_str in relative_dates:
        return relative_dates[input_str]()
    
    another_day_regex = re.compile(r'อีก\s*(\d+)\s*วัน')
    another_day_match = another_day_regex.match(input_str)
    if another_day_match:
        return reference_date + timedelta(days=int(another_day_match.group(1)))
    
    thai_date_parts = re.match(r'(\d+)\s*(\D+)', input_str)
    if thai_date_parts and len(thai_date_parts.groups()) == 2:
        day = int(thai_date_parts.group(1))
        month = thai_months.get(thai_date_parts.group(2).strip(), None)
        if month is not None:
            return datetime(reference_date.year, month + 1, day)
    
    return None

def calculate_check_out(check_in, duration_or_checkout):
    check_in = preprocess_input(check_in)
    duration_or_checkout = preprocess_input(duration_or_checkout)
    
    check_in_date = parse_relative_date(check_in)
    if not check_in_date:
        return "Invalid check-in date"
    
    days_to_add = parse_duration(duration_or_checkout)
    if days_to_add is None:
        specific_date = parse_relative_date(duration_or_checkout)
        if not specific_date:
            return "Invalid durationOrCheckout input"
        days_to_add = (specific_date - check_in_date).days
    
    check_out_date = check_in_date + timedelta(days=days_to_add)
    
    if not check_out_date:
        return "Invalid date calculation"
    
    return format_date(check_out_date)

# Pydantic models for request validation
class CheckInDuration(BaseModel):
    checkIn: str
    durationOrCheckout: str

# FastAPI routes
@app.post("/calculate_checkout/")
def calculate_checkout(data: CheckInDuration):
    check_in = data.checkIn
    duration_or_checkout = data.durationOrCheckout
    
    check_out = calculate_check_out(check_in, duration_or_checkout)
    if check_out == "Invalid check-in date" or check_out == "Invalid durationOrCheckout input":
        raise HTTPException(status_code=400, detail=check_out)
    
    formatted_check_in = format_date(parse_relative_date(check_in))
    
    return {"checkIn": formatted_check_in, "checkOut": check_out}

# Entry point for Uvicorn
if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
