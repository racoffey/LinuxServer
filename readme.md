### Linux Server Project - Venue Catalogue Web Site

This project offers a website based on Python, Flask and an PostGreSQL database to catalogue and serve information about venues.
Anyone can view the venue contents held by the site. The server supports responses in both HTML and JSON.

The site allows venues to be created, updated and deleted, by authenticated users.

Google Plus Sign In is used to authentication and this is the only authentication means presently implemented.



### Set up

The server has been set up with the following configuration:

OS: Ubuntu 16.04.5 LTS
Python: Python 2.7.12 including Flask, SQLAlchemy, Oauth2client and other libraries
DB: PostgreSQL 9.5.14
Server: Apache/2.4.18 (Ubuntu)
WSGI module: 4.3.0-1.1build1

### Running the app

One set up, to run the application the apache server shall be start with then command:

**sudo apache2ctl start**

In your browser visit **http://54.93.239.69.xip.io** to view the app, where venues can be viewed, added, deleted and editted.

A database file is included with the initial files which is called **catalog.db**

If one would like to start with a new database, delete the file **catalog.db** and run the database set up file to initiate a new database.

**python database_setup.py**

### API Endpoints

The API JSON endpoints include the following:

1. To fetch the venue types: **/venueTypes/JSON**

2. To fetch the venues of a particular type: **venues/<int:venuetype_id>/JSON**

3. To fetch details of a particular venue: **/venue/<int:venue_id>/JSON**
