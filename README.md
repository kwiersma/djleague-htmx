# Django HTMX Example App Fantasy Football Draft System

A demonstration project for how HTMX can be used to great a dynamic web application with Django.

## Usage

To run the project locally you will want to install the following:

1. Python 3.12
2. Docker Desktop (to run the DB container)

Once those are installed then you can run the following commands to start up the app.

1. Install pipenv `pip install pipenv`
2. Install Python packages `pipenv install`
3. Copy template `.env` file `cp .env.template .env`
4. Start the DB container in the background `docker compose up -d`
5. Create or update the database structure: `pipenv run python ./manage.py migrate`
6. Run the local server: `pipenv run python manage.py runserver`
7. Load the site at [http://127.0.0.1:8000](http://127.0.0.1:8000)

## Functionality

* Manage a list of Fantasy Teams
* Search and filters players available for drafting
* Track draft results

## Testing

Includes integration level tests for the API and login functionality powered by factory-boy and Django and DRF's built-in testing support.

The tests currently use `unittest` and the Django test runner.

```bash
pipenv run python ./manage.py test --reverse --parallel --keepdb
```

## Pre-commit

If you want to use the `pre-commit` package to run flake8, black, and other checks during the git commit command run the commands below.

```shell
pip install -U pre-commit
pre-commit install
```
