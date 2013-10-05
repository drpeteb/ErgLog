from pyramid.response import Response
from pyramid.httpexceptions import(
    HTTPFound,
    HTTPNotFound,
    )
from pyramid.view import view_config
from pyramid.security import (
    remember,
    forget,
    authenticated_userid,
    )
from pyramid.renderers import render

from sqlalchemy.exc import DBAPIError

from .models import (
    DBI,
    DBSession,
    Rower,
    ErgTypeDistance,
    ErgTypeTime,
    ErgRecordDistance,
    ErgRecordTime,
    )

from .security import get_password

from .erg_time_handling import *

import datetime as dt
import matplotlib.pyplot as plt
import matplotlib.dates as mpl_dates
import StringIO
#import xkcdify

@view_config(route_name='login', renderer='templates/generic_page.pt')
def login(request):
    
    message = 'Please log in.'

    if 'form.login_submitted' in request.params:
        username = request.params['username']
        password = request.params['password']
        if get_password(username) == password:
            headers = remember(request, username)
            return HTTPFound(location=request.route_url('home'),
                             headers=headers)
        message = 'Login failed. Try again.'

    body = render('templates/login.pt', dict(), request)
    return dict(message=message, body=body)



@view_config(route_name='logout')
def logout(request):
    headers = forget(request)
    return HTTPFound(location = request.route_url('login'), headers = headers)


### HOME PAGE VIEW CALLBACKS ###
@view_config(route_name='home', renderer='templates/generic_page.pt', permission='standard')
def home_page(request):
    
    username = authenticated_userid(request)
    rower = DBI.get_rower_by_username(username)
    
    erg_type_distance_list = DBI.list_all(ErgTypeDistance)
    erg_type_time_list = DBI.list_all(ErgTypeTime)
    
    if 'form.add_distance_erg_record' in request.params:
        # Adding a distance erg record
        erg_type_id = request.params['distance_erg_type_id']
        erg_type = DBI.get_thing_by_id(ErgTypeDistance, erg_type_id)
        print erg_type.multiple, erg_type.increment
        return HTTPFound(location = request.route_url('add-distance-erg', multiple=erg_type.multiple, increment=erg_type.increment, username=username))

    elif 'form.add_time_erg_record' in request.params:
        # Adding a time erg record
        try:
            erg_type_id = request.params['time_erg_type_id']
            erg_type = DBI.get_thing_by_id(ErgTypeTime, erg_type_id)
            print erg_type.multiple, erg_type.increment
            return HTTPFound(location = request.route_url('add-time-erg', multiple=erg_type.multiple, increment=erg_type.increment, username=username))
        except KeyError:
            message = 'Ooh-er! Something\'s gone wrong. I don\' recognise that type of erg.'

        '''
        still_good = True
        distance = int(request.params['distance_erg_distance'])

        try:
            time_min = int(request.params['distance_erg_time_min'])
            time_sec = int(request.params['distance_erg_time_sec'])
            time_ten = int(request.params['distance_erg_time_ten'])
        except ValueError:
            message = 'Please use numbers to record your time.'
            still_good = False

        try:
            time = input_time(time_min, time_sec, time_ten)
        except TimeError:
            message = 'That\'s not a valid time. No more than 60 seconds in a minute, 10 tenths in a second, please.'
            still_good = False

        try:
            date = dt.datetime.strptime(request.params['distance_erg_date'], '%Y-%m-%d')
        except ValueError:
            message = 'I don\'t recognise that date.'
            still_good = False
        
        if still_good:
            erg_record = ErgRecordDistance(rower.id, date, time, distance)
            try:
                DBI.add_to_db(erg_record)
                message='Added new distance erg: '+ rower.name + ' rowed ' + str(distance) + 'm in ' + output_time(time) + ' minutes on ' + str(date.date()) + '. Thankyou.'
            except DBAPIError:
                message='Failed to add new erg. You\'ve probably already recorded one for that date. Sorry.'

    elif 'form.time_erg_record_added' in request.params:
        # Adding an erg record
        still_good = True
        time = int(request.params['time_erg_time'])

        try:
            distance = int(request.params['time_erg_distance'])
        except ValueError:
            message = 'Please use numbers to record your distance.'
            still_good = False

        try:
            date = dt.datetime.strptime(request.params['time_erg_date'], '%Y-%m-%d')
        except ValueError:
            message = 'I don\'t recognise that date.'
            still_good = False
        
        if still_good:
            erg_record = ErgRecordTime(rower.id, date, time, distance)
            try:
                DBI.add_to_db(erg_record)
                message='Added new time erg: '+ rower.name + ' rowed ' + str(distance) + 'm in ' + output_time(time) + ' minutes on ' + str(date.date()) + '. Thankyou.'
            except DBAPIError:
                message='Failed to add new erg. You\'ve probably already recorded one for that date. Sorry.'

    elif 'form.view_distance_erg_table' in request.params:
        # Table of distance ergs for a particular rower
        rower_username = request.params['rower_to_table']
        distance = int(request.params['distance_erg_distance'])
        return HTTPFound(location = request.route_url(display_type,rower_id=rower_id))
        '''
    else:
        # Otherwise return default
        message='Welcome to ErgLog, %s. Enjoy your stay.' % rower.name
    
    rower_list = DBI.list_all(Rower)

    temp_dict = dict(username=username,
                     rower_list=rower_list,
                     erg_type_distance_list=erg_type_distance_list,
                     erg_type_time_list=erg_type_time_list,)
    body = render('templates/home.pt', temp_dict, request)
    return dict(message=message, body=body)



### ADD-DISTANCE-ERG PAGE VIEW CALLBACKS ###
@view_config(route_name='add-distance-erg', renderer='templates/generic_page.pt', permission='standard')
def add_distance_erg_page(request):

    # Get the details of the person ENTERING the erg (not necessarily the subject)
    username = authenticated_userid(request)
    rower = DBI.get_rower_by_username(username)    

    # Ensure that the erg type specified by the path actually exists
    try:
        multiple = int(request.matchdict['multiple'])
        increment = int(request.matchdict['increment'])
        DBI.get_erg_type_by_mulitple_and_increment(ErgTypeDistance, multiple, increment)
    except ValueError, DBAPIError:
        return HTTPFound(location = request.route_url('home'))

    # Ensure the subject exists
    try:
        subject = request.matchdict['username']
        rower = DBI.get_rower_by_username(subject)
    except DBAPIError:
        return HTTPFound(location = request.route_url('home'))

    # Check that the subject and username are the same or the username has admin rights






    
    if 'form.distance_erg_record_added' in request.params:
        # Parse the new erg record
        still_good = True

        # Get the date
        try:
            date = dt.datetime.strptime(request.params['distance_erg_date'], '%Y-%m-%d')
        except ValueError:
            message = 'I don\'t recognise that date.'
            still_good = False
        
        # Make a list of block times
        block_time_list = []
        for bb in range(multiple):

            try:
                time_min = int(request.params['min_block_%u'%(bb+1)])
                time_sec = int(request.params['sec_block_%u'%(bb+1)])
                time_ten = int(request.params['ten_block_%u'%(bb+1)])
            except ValueError:
                message = 'Please use numbers to record your time.'
                still_good = False

            try:
                time = input_time(time_min, time_sec, time_ten)
            except TimeError:
                message = 'That\'s not a valid time. No more than 60 seconds in a minute, 10 tenths in a second, please.'
                still_good = False

            # Store the time
            block_time_list.append(time)
            time = sum(block_time_list)

        # Make a new record object and put it in the database
        if still_good:
            erg_record = ErgRecordDistance(rower.id, date, time, increment, multiple, block_time_list)
            try:
                DBI.add_to_db(erg_record)
                message='Added new distance erg: '+ rower.name + ' rowed ' + str(increment*multiple) + 'm in ' + output_time(time) + ' minutes on ' + str(date.date()) + '. Thankyou.'
            except DBAPIError:
                message='Failed to add new erg. You\'ve probably already recorded one for that date. Sorry.'

    else:
        # Otherwise return default
        message='Adding an erg for %s: %sm in blocks of %sm.\n What did you manage?' % (rower.name,str(multiple*increment),str(increment))

    add_distance_url = request.route_url('add-distance-erg', multiple=multiple, increment=increment, username=username)

    min_name_list = ['min_block_%u'%(bb+1) for bb in range(multiple)]
    sec_name_list = ['sec_block_%u'%(bb+1) for bb in range(multiple)]
    ten_name_list = ['ten_block_%u'%(bb+1) for bb in range(multiple)]

    temp_dict = dict(username=username,
                     multiple=multiple,
                     increment=increment,
                     add_distance_url=add_distance_url,
                     min_name_list=min_name_list,
                     sec_name_list=sec_name_list,
                     ten_name_list=ten_name_list,
                     )
    body = render('templates/add_distance_erg.pt', temp_dict, request)
    return dict(message=message, body=body)













### ADMIN PAGE VIEW CALLBACKS ###
@view_config(route_name='admin', renderer='templates/generic_page.pt', permission='admin')
def admin_page(request):

    username = authenticated_userid(request)

    if 'form.rower_added' in request.params:
        # Adding a rower
        rower_username = request.params['username']
        rower_password = request.params['password']
        rower_name = request.params['rower_name']
        rower = Rower(rower_username, rower_password, rower_name)
        try:
            DBI.add_to_db(rower)
            message='Added new rower: ' + rower_name + '. Thankyou.'
        except DBAPIError:
            message='Failed to add new rower. The username or name probably already exists. Sorry.'

    if 'form.rower_removed' in request.params:
        # Removing a rower
        username_for_removal = request.params['rower_for_removal']
        try:
            DBI.remove_rower_by_username(username_for_removal)
            message='Removed a rower: ' + username_for_removal + '. Good riddance.'
        except DBAPIError:
            message='Failed to remove rower. Sorry.'

    elif 'form.admin_promoted' in request.params:
        # Promote an admin from the masses
        username_for_promotion = request.params['rower_for_promotion']
        try:
            DBI.promote_admin(username_for_promotion)
            message='Promoted a new admin.'
        except DBAPIError:
            message='Failed to promote new admin. Sorry.'

    elif 'form.admin_demoted' in request.params:
        # Demote an admin back to where they belong
        username_for_demotion = request.params['admin_for_demotion']
        try:
            DBI.demote_admin(username_for_demotion)
            message='Demoted an admin back to the ranks.'
        except DBAPIError:
            message='Failed to demote admin. Sorry.'

    elif 'form.distance_erg_added' in request.params:
        # Adding a new distance erg
        try:
            increment = int(request.params['increment'])
            multiple = int(request.params['multiple'])
            distance = increment*multiple
            if (distance < 0) or (increment < 0):
                message = 'Ya can\'t row a negative distance.'
            elif (multiple < 1):
                message = 'You must row at least one block.'
            elif distance > 20000:
                message = str(distance) + 'm! That\'s too far.'
            else:
                erg_type = ErgTypeDistance(increment, multiple)
                DBI.add_to_db(erg_type)
                message='Added a new distance erg type: ' + str(distance) + 'm as ' + str(multiple) + ' blocks of ' + str(increment) + 'm. Thankyou.'
        except ValueError:
            message = 'I don\'t understand what you\'ve entered. The incremental distance and multiple thereof must both be positive integers.'
        except DBAPIError:
            message = 'Ooh-er! The database doesn\'t like that. Sorry.'
            
    elif 'form.time_erg_added' in request.params:
        # Adding a new time erg
        try:
            increment = int(request.params['increment'])
            multiple = int(request.params['multiple'])
            time = increment*multiple
            if (time < 0) or (increment < 0):
                message = 'Ya can\'t row a negative time.'
            elif (multiple < 1):
                message = 'You must row at least one block.'
            elif time > 120:
                message = str(time) + 'min! That\'s too long.'
            else:
                erg_type = ErgTypeTime(increment, multiple)
                DBI.add_to_db(erg_type)
                message='Added a new time erg type: ' + str(time) + 'min as ' + str(multiple) + ' blocks of ' + str(increment) + 'min. Thankyou.'
        except ValueError:
            message = 'I don\'t understand what you\'ve entered. The incremental time and multiple thereof must both be positive integers.'
        except DBAPIError:
            message = 'I think that time already exists.'

    else:
        # Otherwise return default
        message='Welcome master. What is your command?'

    rower_list = DBI.list_all(Rower)

    body = render('templates/admin.pt', dict(current_username=username, rower_list=rower_list), request)
    return dict(message=message, body=body)









#@view_config(route_name='table', renderer='templates/table.pt')
#def erg_table(request):
#    # Make a list of ergs to display
#    rower_id = int(request.matchdict['rower_id'])
#    if rower_id == 0:
#        erg_list = DBSession.query(ErgRecord).all()
#    else:
#        erg_list = DBSession.query(ErgRecord).filter_by(rower_id=rower_id).all()
#
#    # If there aren't any, 404 it
#    if not erg_list:
#        return HTTPNotFound('No such page')
#        
#    # Sort and convert to text
#    entries = []
#    erg_list.sort(key=lambda erg: erg.date)
#    for erg in erg_list:
#        date = datetime.datetime.strftime(erg.date,'%Y-%m-%d')
#        rower = DBSession.query(Rower).filter_by(id=erg.rower_id).one().name
#        distance = str(erg.distance)
#        split = str(erg.split)
#        entry = {"date":date, "rower":rower, "distance":distance, "split":split}
#        entries.append(entry)
#
#    return {"entries":entries}


#@view_config(route_name='graph', renderer='templates/graph.pt')
#def erg_graph(request):
#    # Make a list of ergs to display
#    rower_id = int(request.matchdict['rower_id'])
#    if rower_id == 0:
#        erg_list = DBSession.query(ErgRecord).all()
#    else:
#        erg_list = DBSession.query(ErgRecord).filter_by(rower_id=rower_id).all()
#    erg_list.sort(key=lambda erg: erg.date)
#    
#    # Strip out dates and distances
#    dates = []
#    distances = []
#    for erg in erg_list:
#        dates.append(erg.date)
#        distances.append(erg.distance)
#
#    # Create a plot
#    fig = plt.figure()
#    ax = fig.add_subplot(111)
#    ax.plot_date(dates, distances, '-')
#    fig.autofmt_xdate()
#    
#    # Output a string
#    virtual_file = StringIO.StringIO()
#    fig.savefig(virtual_file, format='svg')
#    virtual_file.seek(0)
#    svg_data = virtual_file.buf
#    start_point = svg_data.find('<svg')
#    svg_data = svg_data[start_point:]
#
#    return {"svg_data":svg_data}

