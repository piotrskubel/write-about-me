# About project

Write About Me is a django project designed for media outlets and content creators from games industry.
It automatically imports upcoming releases from external source (wikipedia)
and transfer the data into the database. Users can vote for their favorite titles and suggest games they would like to read about.

# Required packages

To run the project you will need all the packages listed in the requirements.txt file.

# Setting the secrets

First of all you need to set your secret key and/or other sensitive data.
Open the .env file in the main directory and add proper variables.

.env:
```
SECRET_KEY={set your secret key here}
```

settings.py:
```
from decouple import config

...

SECRET_KEY = config('SECRET_KEY')
```
# Using project (localhost)

With database set (by default sqlite3) you should make migrations, create superuser and run the server.
```
python manage.py makemigrations
python manage.py migrate
python manage.py createsuperuser
python manage.py runserver
```
To use superuser functionalities enter:
```
http://127.0.0.1:8000/admin
```
Log in with proper username and password, then go to the index.

# User view (anonymous)

From user perspective there are two main functionalities:
-listing upcoming games for given platform
-voting for the title (limited, you can change the limit in the views.py file)

# Superuser view (authenticated)

From superuser perspective there are additional functionalities:
-deleting and updating entries
-creating and deleting restore points of the database
-reseting games list

# Custom filters

Default data scraping pattern is specified in the data.py file.
Though you can modify 'clean_and_filter()' method to achieve custom results.
