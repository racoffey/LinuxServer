from flask import Flask, render_template, request, redirect
from flask import url_for, flash, jsonify
from flask import session as login_session
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from database_setup import Base, User, VenueType, Venue
app = Flask(__name__)
import random
import string
from oauth2client.client import flow_from_clientsecrets
from oauth2client.client import FlowExchangeError
import httplib2
import json
from flask import make_response
import requests
from functools import wraps


# Create DB based on set up file.
# Important to check the same thread is used not to get conflicts
# engine = create_engine('sqlite:////var/www/FlaskApp/FaskApp/venues.db?check_same_thread=False')
# engine = create_engine('postgresql://usr:pass@localhost:5432/sqlalchemy')
engine = create_engine('postgresql://postgres:postgres@localhost:5432/catalog')
Base.metadata.bind = engine

# Create session towards DB
DBSession = sessionmaker(bind=engine)
session = DBSession()

# AUTHENTICATION SECTION

# Local Google Plus Client Id from file
CLIENT_ID = json.loads(
    open('/var/www/FlaskApp/FlaskApp/client_secrets.json', 'r').read())['web']['client_id']
APPLICATION_NAME = "Restaurant Menu App"

# Login the user.
# Generate client state token for Google Plus and render login template.


@app.route('/login')
def showLogin():
    print("Arrived in showLogin")
    state = ''.join(random.choice(string.ascii_uppercase + string.digits)
                    for x in xrange(32))
    login_session['state'] = state
    return render_template('login.html', STATE=state)


# Authentication user through Google Plus and download users key
# parameters (eg username, email...)
@app.route('/gconnect', methods=['POST'])
def gconnect():
    print("Arrived in gconnect")
    # Validate state token
    if request.args.get('state') != login_session['state']:
        response = make_response(json.dumps('Invalid state parameter.'), 401)
        response.headers['Content-Type'] = 'application/json'
        return response
    # Obtain authorization code
    code = request.data

    try:
        # Upgrade the authorization code into a credentials object
        oauth_flow = flow_from_clientsecrets('client_secrets.json', scope='')
        oauth_flow.redirect_uri = 'postmessage'
        credentials = oauth_flow.step2_exchange(code)
    except FlowExchangeError:
        response = make_response(
            json.dumps('Failed to upgrade the authorization code.'), 401)
        response.headers['Content-Type'] = 'application/json'
        return response

    # Check that the access token is valid.
    access_token = credentials.access_token
    url = ('https://www.googleapis.com/oauth2/v1/tokeninfo?access_token=%s'
           % access_token)
    h = httplib2.Http()
    result = json.loads(h.request(url, 'GET')[1])
    # If there was an error in the access token info, abort.
    if result.get('error') is not None:
        response = make_response(json.dumps(result.get('error')), 500)
        response.headers['Content-Type'] = 'application/json'
        return response

    # Verify that the access token is used for the intended user.
    gplus_id = credentials.id_token['sub']
    if result['user_id'] != gplus_id:
        response = make_response(
            json.dumps("Token's user ID doesn't match given user ID."), 401)
        response.headers['Content-Type'] = 'application/json'
        return response

    # Verify that the access token is valid for this app.
    if result['issued_to'] != CLIENT_ID:
        response = make_response(
            json.dumps("Token's client ID does not match app's."), 401)
        response.headers['Content-Type'] = 'application/json'
        return response

    stored_access_token = login_session.get('access_token')
    stored_gplus_id = login_session.get('gplus_id')
    if stored_access_token is not None and gplus_id == stored_gplus_id:
        response = make_response(json.dumps
                                 ('Current user is already connected.'), 200)
        response.headers['Content-Type'] = 'application/json'
        return response

    # Store the access token in the session for later use.
    login_session['access_token'] = credentials.access_token
    login_session['gplus_id'] = gplus_id

    # Get user info
    userinfo_url = "https://www.googleapis.com/oauth2/v1/userinfo"
    params = {'access_token': credentials.access_token, 'alt': 'json'}
    answer = requests.get(userinfo_url, params=params)

    data = answer.json()

    login_session['username'] = data['name']
    login_session['picture'] = data['picture']
    login_session['email'] = data['email']

    if getUserID(login_session['email']) is None:
        createUser(login_session)

    # Return HTML response
    output = ''
    output += '<h1>Login successful! Welcome, '
    output += login_session['username']
    output += '!</h1>'
    output += '<img src="'
    output += login_session['picture']
    output += ' " style = "\
            width: 300px;\
            height: 300px;\
            border-radius: 150px;\
            -webkit-border-radius: 150px;\
            -moz-border-radius: 150px;"> '
    output += '<h1>Redirecting...'
    flash("you are now logged in as %s" % login_session['username'])
    return output

# Create new user in the database and return the user id


def createUser(login_session):
    newUser = User(name=login_session['username'], email=login_session[
                   'email'], picture=login_session['picture'])
    session.add(newUser)
    session.commit()
    user = session.query(User).filter_by(email=login_session['email']).one()
    return user.id

# Get user info object based on user id


def getUserInfo(user_id):
    user = session.query(User).filter_by(id=user_id).one()
    return user

# Get user id based on user email, if it exists


def getUserID(email):
    try:
        user = session.query(User).filter_by(email=email).one()
        return user.id
    except Exception:
        return None

# Disconnect Google Plus user as part of logout and remove relevant parameters
# from the login session


@app.route('/gdisconnect')
def gdisconnect():
    access_token = login_session.get('access_token')
    if access_token is None:
        response = make_response(json.dumps('Current user not connected.'),
                                 401)
        response.headers['Content-Type'] = 'application/json'
        return response
    url = 'https://accounts.google.com/o/oauth2/revoke?token=%s' % \
        login_session['access_token']
    h = httplib2.Http()
    result = h.request(url, 'GET')[0]
    if result['status'] == '200':
        del login_session['access_token']
        del login_session['gplus_id']
        del login_session['username']
        del login_session['email']
        del login_session['picture']
        response = make_response(json.dumps('Successfully disconnected.'), 200)
        response.headers['Content-Type'] = 'application/json'
        return response
    else:
        response = make_response(json.dumps('Failed to revoke token for given\
                user.', 400))
        response.headers['Content-Type'] = 'application/json'
        return response


# Checks if user is logged in and if not redirects to login page


def login_required(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if 'username' not in login_session:
            return redirect(url_for('showLogin'))
        return f(*args, **kwargs)
    return decorated_function


# Show types of venues


@app.route('/')
@app.route('/venuetypes')
def showVenueTypes():
    venue_types = session.query(VenueType)
    items = venue_types
    return render_template('venuetypes.html',
                           items=items,
                           login_session=login_session)


# Return html template for for creating venue type and processing returned form


@app.route('/new_venue_type', methods=['GET', 'POST'])
#@login_required
def createVenueType():

    if request.method == 'POST':
#        newItem = VenueType(type=request.form['name'],
#                            user_id=getUserID(login_session["email"]))
	newUser = User(name="rob", email="racoffey@gmail.com", picture="")
    	session.add(newUser)
    	session.commit()
	newItem = VenueType(type=request.form['name'],user_id=1)
        session.add(newItem)
        session.commit()
        flash("New venue type created!")
        return redirect(url_for('showVenueTypes'))
    else:
        return render_template('newvenuetype.html',
                               login_session=login_session)

# Shows venues of a certain type eg bars, cafes, etc


@app.route('/venues/<int:venuetype_id>', methods=['GET', 'POST'])
def showVenueType(venuetype_id):
    venues = session.query(Venue).filter_by(type_id=venuetype_id)
    venuetype = session.query(VenueType).filter_by(id=venuetype_id).first()
    user = session.query(User).filter_by(id=venuetype.user_id).first()
    return render_template('venues.html', venues=venues, venuetype=venuetype,
                           user=user, login_session=login_session)

# Return html template for for editing venue type and processing returned form


@app.route('/edit_venuetype/<int:venuetype_id>', methods=['GET', 'POST'])
@login_required
def editVenueType(venuetype_id):
    editedVenueType = session.query(VenueType).filter_by(id=venuetype_id).one()
    user = session.query(User).filter_by(id=editedVenueType.user_id).first()
    # Check if user has created the venue type and if not redirect
    if user.name != login_session['username']:
        flash("One can only edit venue types one has created!")
        return redirect(url_for('showVenueTypes'))
    if request.method == 'POST':
        editedVenueType.type = request.form['name']
        session.add(editedVenueType)
        session.commit()
        flash("Venue type updated!")
        return redirect(url_for('showVenueTypes'))
    else:
        return render_template('editvenuetype.html', venuetype=editedVenueType,
                               user=user,
                               login_session=login_session)


# Deletes venue types


@app.route('/delete_venuetype/<int:venuetype_id>', methods=['GET', 'POST'])
@login_required
def deleteVenueType(venuetype_id):
    venueType = session.query(VenueType).filter_by(id=venuetype_id).one()
    user = session.query(User).filter_by(id=venueType.user_id).first()
    # Check if user has created the venue type
    if user.name != login_session['username']:
        flash("One can only edit venue types one has created!")
        return redirect(url_for('showVenueTypes'))
    session.delete(venueType)
    session.commit()
    flash("Venue type deleted!")
    return redirect(url_for('showVenueTypes'))

# Returns html template for for creating venue  and processing returned form


@app.route('/new_venue/<int:venuetype_id>', methods=['GET', 'POST'])
@login_required
def createVenue(venuetype_id):
    if request.method == 'POST':
        newItem = Venue(name=request.form['name'],
                        streetname=request.form['streetname'],
                        postcode=request.form['postcode'],
                        description=request.form['description'],
                        type_id=venuetype_id,
                        user_id=getUserID(login_session['email']))
        session.add(newItem)
        session.commit()
        flash("New venue created!")
        return redirect(url_for('showVenueType', venuetype_id=venuetype_id,
                        login_session=login_session))
    else:
        venuetype = session.query(VenueType).filter_by(id=venuetype_id).one()
        return render_template('newvenue.html', venuetype=venuetype,
                               login_session=login_session)

# Shows a selected venue


@app.route('/venue/<int:venue_id>', methods=['GET', 'POST'])
def showVenue(venue_id):
    venue = session.query(Venue).filter_by(id=int(venue_id)).one()
    user = session.query(User).filter_by(id=venue.user_id).first()
    return render_template('venue.html', venue=venue, user=user,
                           login_session=login_session)

# Returns html template for for editing venue  and processing returned form


@app.route('/edit_venue/<int:venue_id>', methods=['GET', 'POST'])
@login_required
def editVenue(venue_id):

    editedVenue = session.query(Venue).filter_by(id=venue_id).one()
    user = session.query(User).filter_by(id=editedVenue.user_id).first()

    # Check if user has created the venue
    if user.name != login_session['username']:
        flash("One can only edit venue types one has created!")
        return redirect(url_for('showVenueTypes'))

    if request.method == 'POST':
        editedVenue.name = request.form['name']
        editedVenue.streetname = request.form['streetname']
        editedVenue.postcode = request.form['postcode']
        editedVenue.description = request.form['description']
        session.add(editedVenue)
        session.commit()
        flash("Venue updated!")
        return redirect(url_for('showVenue', venue_id=venue_id))
    else:
        return render_template('editvenue.html', venue=editedVenue, user=user,
                               login_session=login_session)

# Deletes venue


@app.route('/delete_venue/<int:venue_id>', methods=['GET', 'POST'])
@login_required
def deleteVenue(venue_id):

    venue = session.query(Venue).filter_by(id=venue_id).first()
    user = session.query(User).filter_by(id=venue.user_id).first()

    # Check if user has created the venue
    if user.name != login_session['username']:
        flash("One can only edit venue types one has created!")
        return redirect(url_for('showVenueTypes'))

    session.delete(venue)
    session.commit()
    venuetype = session.query(VenueType).filter_by(id=venue.type_id).first()
    venues = session.query(Venue).filter_by(type_id=venue.type_id)
    return render_template('venues.html', venues=venues, venuetype=venuetype,
                           user=user,
                           login_session=login_session)


# JSON APIs to view Venue Information

# Returns venue types in JSON format


@app.route('/venueTypes/JSON')
def showVenueTypesJSON():
    venue_types = session.query(VenueType).all()
    return jsonify(venue_types=[i.serialize for i in venue_types])

# Returns venues of a certain type in JSON format


@app.route('/venues/<int:venuetype_id>/JSON')
def showVenueTypeJSON(venuetype_id):
    venues = session.query(Venue).filter_by(type_id=venuetype_id).all()
    return jsonify(venues=[i.serialize for i in venues])

# Returns a venue in JSON format


@app.route('/venue/<int:venue_id>/JSON')
def showVenueJSON(venue_id):
    venue = session.query(Venue).filter_by(id=int(venue_id)).one()
    user = session.query(User).filter_by(id=venue.user_id).first()
    return jsonify(venue=[venue.serialize])


# Main run code
app.secret_key = 'super_secret_key'
if __name__ == '__main__':
    connect_args = {'check_same_thread': False},
    app.secret_key = 'super_secret_key'
    app.debug = True
    app.run()
