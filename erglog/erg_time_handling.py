class TimeError(Exception):
    pass

def input_time(min, sec, ten):
    if (sec > 59) or (ten > 9):
        raise TimeError
    time = 600*min + 10*sec + ten
    return time

def output_time(time):
    min = (time-(time%600))/600
    time = time%600
    sec = (time-(time%10))/10
    ten = time%10
    time_string = str(min) + ':' + str(sec).zfill(2) + '.' + str(ten)
    return time_string
    
