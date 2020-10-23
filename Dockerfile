FROM python:3.7
WORKDIR /app
COPY Pipfile* ./
RUN pip install pipenv
RUN pipenv install --system --deploy
COPY . ./
CMD gunicorn "thepost.wsgi:application" --bind 0.0.0.0:8000 
