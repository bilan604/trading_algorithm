
from datetime import datetime
current_datetime = datetime.now()
print(current_datetime)

def get_hours_difference(datetime_str1, datetime_str2):
    # positive when datetime_str1 > datetime_str2
    
    # Convert the strings to datetime objects
    dt1 = datetime.fromisoformat(datetime_str1)
    dt2 = datetime.fromisoformat(datetime_str2)

    # Calculate the difference
    datediff = dt1 - dt2

    # Get total difference in hours
    hours_diff = (datediff.days * 24) + (datediff.seconds // 3600)
    print("Total Hours Difference:", hours_diff)
    return hours_diff
