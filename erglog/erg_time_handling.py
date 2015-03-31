class TimeError(Exception):
    pass

def input_time(min, sec, ten):
    if (sec > 59) or (ten > 9):
        raise TimeError
    time = 600*min + 10*sec + ten
    return time

def output_time(time):
    min = int( (time-(time%600))/600 )
    time = time%600
    sec = int( (time-(time%10))/10 )
    ten = int(time%10)
    time_string = '{0}:{1}.{2}'.format(min,sec,ten)  #str(min) + ':' + str(sec).zfill(2) + '.' + str(ten)
    return time_string
    
