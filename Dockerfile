FROM python:3.12

COPY ./requirements.txt /var/www/requirements.txt
COPY ./app /app

RUN pip install --no-cache-dir -r /var/www/requirements.txt