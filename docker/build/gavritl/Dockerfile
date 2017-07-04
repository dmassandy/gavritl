FROM python:3.6.1-slim

# Update aptitude with new repo
RUN apt-get update

# Install software 
RUN apt-get install -y git

RUN pip install pyaes

ADD https://api.github.com/repos/dmassandy/Telethon/git/refs/heads/master version.json
RUN git clone -bmaster https://github.com/dmassandy/Telethon.git

WORKDIR /Telethon

RUN python setup.py gen_tl

RUN python setup.py install

RUN mkdir /gavritl-app

WORKDIR /gavritl-app

ADD requirements.txt /gavritl-app/requirements.txt

RUN pip install -r requirements.txt

ADD start.sh /start.sh

VOLUME /gavritl-app

# EXPOSE port 8000 to allow communication to/from server
EXPOSE 8000

CMD ["start.sh"]