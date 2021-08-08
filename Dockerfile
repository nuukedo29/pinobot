FROM python:3.9

RUN mkdir -p /app
WORKDIR /app

RUN curl -sL https://deb.nodesource.com/setup_14.x | bash -
RUN apt install -y openssl nodejs nginx
RUN npm install -g nodemon

ADD ./requirements.txt /app
RUN python3 -m pip install --upgrade pip
RUN python3 -m pip install -r requirements.txt
RUN useradd -s /bin/false nginx

ADD . /app

ENV PYTHONDONTWRITEBYTECODE=1

CMD python3 pinobot.py 