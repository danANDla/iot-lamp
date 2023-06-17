from datetime import datetime
now = datetime.now()
dawn_offset = 2 
print(now.hour * 60 + now.minute + dawn_offset)
