# syntax=docker/dockerfile:1
FROM python:3.12-slim-bookworm

# Lint with Hadolint:
# docker run --rm -i hadolint/hadolint < Dockerfile

# Set environment variables
ENV PYTHONDONTWRITEBYTECODE 1
ENV PYTHONUNBUFFERED 1
ENV PYTHONIOENCODING UTF-8

# Set work directory
WORKDIR /code

# Install OS security updates
RUN apt-get update && apt-get -y upgrade &&  \
    apt-get clean && rm -rf /var/lib/apt/lists/*

# create the app user
RUN addgroup --system app && adduser --ingroup app --home /home/app --shell /bin/sh app

# create the appropriate directories
ENV HOME=/home/app
ENV APP_HOME=/home/app/web
RUN mkdir $APP_HOME
# Setup empty ~/.ssh directory
RUN mkdir $HOME/.ssh
WORKDIR $APP_HOME

# Install dependencies
COPY ./Pipfile .
COPY ./Pipfile.lock .
RUN pip install --upgrade pip setuptools wheel --no-cache-dir &&  \
    pip install pipenv--no-cache-dir &&  \
    pipenv install --ignore-pipfile

# copy project
COPY . $APP_HOME

# chown all the files to the app user
RUN chown -R app:app $APP_HOME && chown -R app:app $HOME/.ssh && chmod 700 $HOME/.ssh

# change to the app user
USER app

# Collect static files
RUN export DJANGO_SETTINGS_MODULE=djleague.settings &&  \
    pipenv run ./manage.py collectstatic --no-input

# https://twitter.com/kjrjay/status/1532624896509067264
# https://github.com/morninj/django-docker/blob/master/Dockerfile
# CMD ["supervisord", "-n", "-c", "./supervisord.ini"]
# CMD ["pipenv", "run", "gunicorn", "djleague.wsgi:application", "--timeout", "120", "--workers", "3"]
CMD bash -c ". entrypoint.sh"
