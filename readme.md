# Linux Server Project - Venue Catalogue Web Site #

This project offers a website based on Python, Flask and an PostGreSQL database to catalogue and serve information about venues.
Anyone can view the venue contents held by the site. The server supports responses in both HTML and JSON.

The site allows venues to be created, updated and deleted, by authenticated users.

Google Plus Sign In is used to authentication and this is the only authentication means presently implemented.



## Set up ##

The server has been set up with the following configuration:

HW: AWS Lightsail Virtual Instance
OS: Ubuntu 16.04.5 LTS
Python: Python 2.7.12 including Flask, SQLAlchemy, Oauth2client and other libraries
DB: PostgreSQL 9.5.14
Server: Apache/2.4.18 (Ubuntu)
WSGI module: 4.3.0-1.1build1


### Server set up ###

Install the Apache server using the following command:

sudo apt-get install apache2-binÂ`


### Database set up ###

Install the PostgreSQL server using the following command:
`sudo apt-get install postgresql`

The postgresql user and password can be set up with the following command sequence:
`sudo -u postgres psql postgres`

And then:
`password: \password postgres`

To exit sql prompt:
`\q`

The **catalog.db** database needs to be created with the following command:
`sudo -u postgres createdb catalog.db`

The database can then be set up by running the following python script:
`python database_setup.py`

Then the database should be ready to go.

### Web Server Gateway set up ###
To be able to redirect the incoming HTML requests to the Flask application, install the mod_wsgi application handler:
`sudo apt-get install libapache2-mod-wsgi`

To tell the handler where to find the Flask application edit the following file:
`/etc/apache2/sites-enabled/000-default.conf`

For now, add the following line at the end of the ** <VirtualHost *:80>** block, right before the closing
 ** </VirtualHost>** line: **WSGIScriptAlias / /var/www/html/FlaskApp.ws$

A .wsgi file shall be created:
`sudo nano /var/www/FlaskApp/flaskapp.wsgi`

With the following content:

`
import sys
import logging
logging.basicConfig(stream=sys.stderr)
sys.path.insert(0,"/var/www/FlaskApp/")

from FlaskApp import app as application
`

See 3rd part link to Flask Pooco Org for more information.

Apache should then be restarted with:
`sudo apache2ctl restart`

### Installing the app ###
The application can be installed to the following directory by cloning it to the following responsitory
from Github:
`/var/www/FlaskApp/FlaskApp`

The git respository for this app can be found here:
`https://github.com/racoffey/LinuxServer.git`

### 3rd party resources ###

Here are some important links to 3rd party resources used in the set up of this project.

For the virtual environment: https://lightsail.aws.amazon.com/

To deploy Flash in Apache with mod_wsgi: http://flask.pocoo.org/docs/0.12/deploying/mod_wsgi/

The following site has been used to allow a fully qualified domain name to be used when only the IP address is available: http://xip.io

For help finding Apache logs when operating the server: https://askubuntu.com/questions/14763/where-are-the-apache-and-php-log-files


### Administration ###

The server can be reached via SSH using port 2200 on the IP address 54.93.239.69. The public key will be provided separately.


## Running the app ##

One set up, to run the application the apache server shall be start with then command:

`sudo apache2ctl start`

In your browser visit **http://54.93.239.69.xip.io** to view the app, where venues can be viewed, added, deleted and editted.


## API Endpoints ##

The API JSON endpoints include the following:

1. To fetch the venue types: **/venueTypes/JSON**

2. To fetch the venues of a particular type: **venues/<int:venuetype_id>/JSON**

3. To fetch details of a particular venue: **/venue/<int:venue_id>/JSON**
