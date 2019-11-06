FROM tiangolo/uwsgi-nginx-flask:python3.6-alpine3.7
RUN apk --update add bash vim
ENV STATIC_URL /
ENV STATIC_PATH /static
COPY ./requirements.txt /app/requirements.txt
RUN pip install -r /app/requirements.txt && rm /app/requirements.txt
