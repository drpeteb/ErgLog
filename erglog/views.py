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

from sqlalchemy.exc import DBAPIError, InvalidRequestError

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
from matplotlib.ticker import FuncFormatter
import io
#import xkcdify


def time_labeller(time,ii):
    (m,s,t) = explode_time(time)
    return '{0}:{1:=02}'.format(m,s)


### LOGIN PAGE VIEW CALLBACKS ###
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
        try:
            erg_type_id = int(request.params['distance_erg_type_id'])
            erg_type = DBI.get_thing_by_id(ErgTypeDistance, erg_type_id)
            return HTTPFound(location = request.route_url('add-distance-erg', erg_type_id=str(erg_type_id), username=username))
        except [KeyError,DBAPIError]:
            message = 'Ooh-er! Something\'s gone wrong. I don\'t recognise that type of erg.'

    elif 'form.add_time_erg_record' in request.params:
        # Adding a time erg record
        try:
            erg_type_id = int(request.params['time_erg_type_id'])
            erg_type = DBI.get_thing_by_id(ErgTypeTime, erg_type_id)
            return HTTPFound(location = request.route_url('add-time-erg', erg_type_id=str(erg_type_id), username=username))
        except [KeyError,DBAPIError]:
            message = 'Ooh-er! Something\'s gone wrong. I don\'t recognise that type of erg.'

    elif 'form.view_individual_distance_ergs' in request.params:
        # View distance erg records for a single rower
        try:
            erg_type_id = int(request.params['distance_erg_type_id'])
            erg_type = DBI.get_thing_by_id(ErgTypeDistance, erg_type_id)
            rower_to_view = request.params['rower_to_view']
            return HTTPFound(location = request.route_url('view-distance-individual', erg_type_id=str(erg_type_id), username=rower_to_view))
        except [KeyError,DBAPIError]:
            message = 'Ooh-er! Something\'s gone wrong. I don\'t recognise that type of erg.'

    elif 'form.view_individual_time_ergs' in request.params:
        # View time erg records for a single rower
        try:
            erg_type_id = int(request.params['time_erg_type_id'])
            erg_type = DBI.get_thing_by_id(ErgTypeTime, erg_type_id)
            rower_to_view = request.params['rower_to_view']
            return HTTPFound(location = request.route_url('view-time-individual', erg_type_id=str(erg_type_id), username=rower_to_view))
        except [KeyError,DBAPIError]:
            message = 'Ooh-er! Something\'s gone wrong. I don\'t recognise that type of erg.'

    elif 'form.view_group_distance_ergs' in request.params:
        # View distance erg records for a many rowers
        try:
            erg_type_id = int(request.params['distance_erg_type_id'])
            erg_type = DBI.get_thing_by_id(ErgTypeDistance, erg_type_id)
            return HTTPFound(location = request.route_url('view-distance-group', erg_type_id=str(erg_type_id)))
        except [KeyError,DBAPIError]:
            message = 'Ooh-er! Something\'s gone wrong. I don\'t recognise that type of erg.'


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
            distance = int(request.params['distance'])
            if (distance < 0):
                message = 'Ya can\'t row a negative distance.'
            elif distance > 50000:
                message = str(distance) + 'm! That\'s too far.'
            else:
                erg_type = ErgTypeDistance(distance)
                DBI.add_to_db(erg_type)
                message='Added a new distance erg type: ' + str(distance) + 'm. Thankyou.'
        except ValueError:
            message = 'I don\'t understand what you\'ve entered. The distance must be a positive integer.'
        except DBAPIError:
            message = 'Ooh-er! The database doesn\'t like that. Sorry.'
            
    elif 'form.time_erg_added' in request.params:
        # Adding a new time erg
        try:
            time = int(request.params['time'])
            if (time < 0):
                message = 'Ya can\'t row for a negative amount of time.'
            elif time > 120:
                message = str(time) + 'min! That\'s too long.'
            else:
                erg_type = ErgTypeTime(time)
                DBI.add_to_db(erg_type)
                message='Added a new time erg type: ' + str(time) + 'min. Thankyou.'
        except ValueError:
            message = 'I don\'t understand what you\'ve entered. The time must be a positive integer.'

        except DBAPIError:
            message = 'Ooh-er! The database doesn\'t like that. Sorry.'

    else:
        # Otherwise return default
        message='Welcome master. What is your command?'

    rower_list = DBI.list_all(Rower)

    body = render('templates/admin.pt', dict(current_username=username, rower_list=rower_list), request)
    return dict(message=message, body=body)





### ADD-DISTANCE-ERG PAGE VIEW CALLBACKS ###
@view_config(route_name='add-distance-erg', renderer='templates/generic_page.pt', permission='standard')
def add_distance_erg_page(request):

    # Get the details of the person ENTERING the erg (not necessarily the subject)
    username = authenticated_userid(request)    

    # Ensure that the erg type specified by the path actually exists
    try:
        erg_type_id = int(request.matchdict['erg_type_id'])
        erg_type = DBI.get_thing_by_id(ErgTypeDistance, erg_type_id)
    except [ValueError,DBAPIError]:
        return HTTPNotFound('No such page')

    # Ensure the subject exists
    try:
        subject = request.matchdict['username']
        rower = DBI.get_rower_by_username(subject)
    except DBAPIError:
        return HTTPNotFound('No such page')

    # Check that the subject and username are the same or the username has admin rights
    ### ADD THIS CHECK ###

    if 'form.distance_erg_record_added' in request.params:
        # Parse the new erg record
        still_good = True

        # Get the date
        try:
            date = dt.datetime.strptime(request.params['distance_erg_date'], '%Y-%m-%d')
        except ValueError:
            message = 'I don\'t recognise that date.'
            still_good = False

        try:
            time_min = int(request.params['mins'])
            time_sec = int(request.params['secs'])
            time_ten = int(request.params['tens'])
        except ValueError:
            message = 'Please use numbers to record your time.'
            still_good = False

        try:
            time = input_time(time_min, time_sec, time_ten)
        except TimeError:
            message = 'That\'s not a valid time. No more than 60 seconds in a minute, 10 tenths in a second, please.'
            still_good = False

        # Make a new record object and put it in the database
        if still_good:
            erg_record = ErgRecordDistance(rower.id, date, time, erg_type_id)
            try:
                DBI.add_to_db(erg_record)
                message='Added new distance erg: {0} rowed {1!s}m in {2} on {3!s}. Thankyou.'.format(rower.name, int(erg_type.distance), output_time(time), date.date())
            except DBAPIError:
                message='Failed to add new erg. You\'ve probably already recorded one for that date. Sorry.'

    else:
        # Otherwise return default
        message='Go on then. How did it go?'

    add_distance_url = request.route_url('add-distance-erg', erg_type_id=erg_type_id, username=username)

    temp_dict = dict(username=username,
                     name=rower.name,
                     distance=erg_type.distance,
                     add_distance_url=add_distance_url
                     )
    body = render('templates/add_distance_erg.pt', temp_dict, request)
    return dict(message=message, body=body)



### ADD-TIME-ERG PAGE VIEW CALLBACKS ###
@view_config(route_name='add-time-erg', renderer='templates/generic_page.pt', permission='standard')
def add_time_erg_page(request):

    # Get the details of the person ENTERING the erg (not necessarily the subject)
    username = authenticated_userid(request)    

    # Ensure that the erg type specified by the path actually exists
    try:
        erg_type_id = int(request.matchdict['erg_type_id'])
        erg_type = DBI.get_thing_by_id(ErgTypeTime, erg_type_id)
    except [ValueError,DBAPIError]:
        return HTTPNotFound('No such page')

    # Ensure the subject exists
    try:
        subject = request.matchdict['username']
        rower = DBI.get_rower_by_username(subject)
    except DBAPIError:
        return HTTPNotFound('No such page')

    # Check that the subject and username are the same or the username has admin rights
    ### ADD THIS CHECK ###

    if 'form.distance_erg_record_added' in request.params:
        # Parse the new erg record
        still_good = True

        # Get the date
        try:
            date = dt.datetime.strptime(request.params['time_erg_date'], '%Y-%m-%d')
        except ValueError:
            message = 'I don\'t recognise that date.'
            still_good = False

        try:
            distance = int(request.params['distance'])
        except ValueError:
            message = 'Please use numbers to record your distance.'
            distance = 0
            still_good = False

        if distance < 0:
            message = 'You rowed backwards...!? Try again.'
            still_good = False

        # Make a new record object and put it in the database
        if still_good:
            erg_record = ErgRecordTime(rower.id, date, distance, erg_type_id)
            try:
                DBI.add_to_db(erg_record)
                message='Added new time erg: {0} rowed {1}m in {2} on {3!s}. Thankyou.'.format(rower.name, distance, erg_type.time, date.date())
            except DBAPIError:
                message='Failed to add new erg. You\'ve probably already recorded one for that date. Sorry.'

    else:
        # Otherwise return default
        message='Go on then. How did it go?'

    add_time_url = request.route_url('add-time-erg', erg_type_id=erg_type_id, username=username)

    temp_dict = dict(username=username,
                     name=rower.name,
                     time=erg_type.time,
                     add_time_url=add_time_url
                     )
    body = render('templates/add_time_erg.pt', temp_dict, request)
    return dict(message=message, body=body)




### VIEW-DISTANCE-INDIVIDUAL PAGE VIEW CALLBACKS ###
@view_config(route_name='view-distance-individual', renderer='templates/generic_page.pt', permission='standard')
def view_distance_individual_page(request):

    # Ensure that the erg type specified by the path actually exists
    try:
        erg_type_id = int(request.matchdict['erg_type_id'])
        erg_type = DBI.get_thing_by_id(ErgTypeDistance, erg_type_id)
    except [ValueError,DBAPIError]:
        return HTTPNotFound('No such page')

    # Ensure the subject exists
    try:
        subject = request.matchdict['username']
        rower = DBI.get_rower_by_username(subject)
    except DBAPIError:
        return HTTPNotFound('No such page')

    # Get a list of ergs
    try:
        erg_list = DBI.get_ergs_by_type_and_rower(ErgRecordDistance, erg_type_id, rower.id)
    except DBAPIError:
        return HTTPNotFound('No such page')

    # Sort ergs by date
    erg_list.sort(key=lambda erg: erg.date)
    
    # Strip out dates and distances
    dates = [ee.date for ee in erg_list]
    times = [ee.time for ee in erg_list]

    # Create a plot
    fig = plt.figure()
    ax = fig.add_subplot(1,1,1)
    ax.plot(dates, times, '-ok')
    fig.autofmt_xdate()
    ax.yaxis.set_major_formatter(FuncFormatter(time_labeller))
    
    # Output a string
    fig_stream = io.StringIO()
    fig.savefig(fig_stream, format='svg')
    fig_stream.seek(0)
    svg_data = ''.join(fig_stream.readlines())
    start_point = svg_data.find('<svg')
    svg_data = svg_data[start_point:]

    # Create page
    body = render('templates/graph.pt', dict(svg_data=svg_data), request)
    message = 'Showing {}m ergs for {}'.format(erg_type.distance, rower.name)

    return dict(message=message, body=body)



### VIEW-TIME-INDIVIDUAL PAGE VIEW CALLBACKS ###
@view_config(route_name='view-time-individual', renderer='templates/generic_page.pt', permission='standard')
def view_time_individual_page(request):

    # Ensure that the erg type specified by the path actually exists
    try:
        erg_type_id = int(request.matchdict['erg_type_id'])
        erg_type = DBI.get_thing_by_id(ErgTypeTime, erg_type_id)
    except [ValueError,DBAPIError]:
        return HTTPNotFound('No such page')

    # Ensure the subject exists
    try:
        subject = request.matchdict['username']
        rower = DBI.get_rower_by_username(subject)
    except DBAPIError:
        return HTTPNotFound('No such page')

    # Get a list of ergs
    try:
        erg_list = DBI.get_ergs_by_type_and_rower(ErgRecordTime, erg_type_id, rower.id)
    except DBAPIError:
        return HTTPNotFound('No such page')

    # Sort ergs by date
    erg_list.sort(key=lambda erg: erg.date)
    
    # Strip out dates and distances
    dates     = [ee.date     for ee in erg_list]
    distances = [ee.distance for ee in erg_list]

    # Create a plot
    fig = plt.figure()
    ax = fig.add_subplot(1,1,1)
    ax.plot(dates, distances, '-ok')
    ax.set_ylabel('m')
    fig.autofmt_xdate()
    
    # Output a string
    fig_stream = io.StringIO()
    fig.savefig(fig_stream, format='svg')
    fig_stream.seek(0)
    svg_data = ''.join(fig_stream.readlines())
    start_point = svg_data.find('<svg')
    svg_data = svg_data[start_point:]

    # Create page
    body = render('templates/graph.pt', dict(svg_data=svg_data), request)
    message = 'Showing {} min ergs for {}'.format(erg_type.time, rower.name)

    return dict(message=message, body=body)

######################
### VIEW-DISTANCE-GROUP PAGE VIEW CALLBACKS ###
@view_config(route_name='view-distance-group', renderer='templates/generic_page.pt', permission='standard')
def view_distance_group_page(request):

    # Ensure that the erg type specified by the path actually exists
    try:
        erg_type_id = int(request.matchdict['erg_type_id'])
        erg_type = DBI.get_thing_by_id(ErgTypeDistance, erg_type_id)
    except [ValueError,DBAPIError]:
        return HTTPNotFound('No such page')
    
    # Get a list of all rowers
    try:
        all_rower_list = DBI.list_all(Rower)
    except DBAPIError:
        return HTTPNotFound('No such page')

    # Get a list of rowers to plot
    if 'form.submit_rower_list' in request.params:
        rower_ids = request.params.getall('rowers_to_plot')
        print(rower_ids)
        try:
            rower_list = [DBI.get_thing_by_id(Rower, int(idstr)) for idstr in rower_ids]
        except DBAPIError:
            return HTTPNotFound('No such page')
    else:
        rower_list = all_rower_list
        
    
    # Get a list of ergs for each rower
    try:
        rower_erg_list = []
        for rower in rower_list:
            rower_erg_list.append( DBI.get_ergs_by_type_and_rower(ErgRecordDistance, erg_type_id, rower.id) )
    except DBAPIError:
        return HTTPNotFound('No such page')

    # Sort ergs by date
    for el in rower_erg_list:
        el.sort(key=lambda erg: erg.date)
    
    # Make a list of colours
    colours = plt.get_cmap('jet')(np.linspace(0, 1.0, len(rower_list)))
    print(colours)
    
    # Create a plot
    fig = plt.figure(figsize=(10,8))
    ax = fig.add_axes([0.1,0.15,0.6,0.8])

    # Draw all the ergs
    for rr in range(len(rower_list)):
        rower = rower_list[rr]
        el = rower_erg_list[rr]
        ax.plot([ee.date for ee in el], [ee.time for ee in el], '-o', color=colours[rr], label=rower.name)

    # Format
    #box = ax.get_position()
    #ax.set_position([box.x0, box.y0, 0.5*box.width, box.height])
    ax.legend(loc='center left', bbox_to_anchor=(1, 0.5))
    fig.autofmt_xdate()
    ax.yaxis.set_major_formatter(FuncFormatter(time_labeller))
    
    # Output a string
    fig_stream = io.StringIO()
    fig.savefig(fig_stream, format='svg')
    fig_stream.seek(0)
    svg_data = ''.join(fig_stream.readlines())
    start_point = svg_data.find('<svg')
    svg_data = svg_data[start_point:]
    
    # Get page url
    view_group_url = request.route_url('view-distance-group', erg_type_id=erg_type_id)
    
    # Create page
    temp_dict = dict(svg_data=svg_data,
                     view_group_url=view_group_url,
                     rower_list=all_rower_list)
    body = render('templates/multi-graph.pt', temp_dict, request)
    message = 'Showing {}m ergs'.format(erg_type.distance)

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

