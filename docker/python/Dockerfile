FROM python:3.6

ENV PYTHONUNBUFFERED 1

WORKDIR /var/www/app

RUN mkdir -p /var/www/app/

COPY . /var/www/app/

ADD requirements.txt /var/www

RUN pip install -r /var/www/requirements.txt
ENTRYPOINT ["python", "/var/www/app/manage.py"]
