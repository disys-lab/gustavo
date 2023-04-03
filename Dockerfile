#GV=v0.2.0-beta.14 docker build -t gustavo_base:$GV --build-arg GUSTAVO_VERSION=$GV .
#export GV=v0.2.0-beta.14 && docker-compose -f config_files/docker-compose.yml up -d

FROM ubuntu:22.04

RUN apt-get -y update && apt-get -y upgrade

RUN apt-get -y install build-essential

RUN apt-get -y install python3 python3-pip python3-numpy zlib1g-dev

ARG GUSTAVO_VERSION=v0.2.0-beta.14 //Default value provided

RUN pip3 install --extra-index-url https://pypi.fury.io/osu-home-stri/ gustavo==${GUSTAVO_VERSION}

COPY ./tests/ /home/tests/
