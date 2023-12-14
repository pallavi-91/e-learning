# Sailnorth

## Setup and Configurations

### Backend:
1. Setup virtualenv. this app uses `Python 3.8.0 or above`
2. Clone from repository
3. Activate virtualenv and install the dependencies. `pip install -r requirements.txt`
3.1. for the database. we need to use `postgresql` as JSONField is not supported by other SQL.
4. Execute `python manage.py migrate`
5. Run the server. `python manage.py runserver`

### Frontend:
1. Install Angular-CLI and Nodejs. `npm install -g @angular/cli`
    - Angular-CLI 12.2.14 or higher
    - Node 12.20 (installing higher version may cause some issues)
2. Install dependencies for the frontend. Go to `assets/fe` and Execute `npm install`
3. Build. `ng build`. if you want to make changes on the scripts you need to add `--watch`


*NOTE*: Make sure to create a `local_settings.py` containing these configurations. (PLEASE DO NOT PUSH IT IN THE REMOTE REPO)

```
DEBUG = True

ALLOWED_HOSTS = ('*',)

IS_PRODUCTION = False

DATABASES (same format on settings.py)
```