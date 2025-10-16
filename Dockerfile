#GV=v0.2.0-beta.14 docker build -t gustavo_base:$GV --build-arg GUSTAVO_VERSION=$GV .
#export GV=v0.2.0-beta.14 && docker-compose -f config_files/docker-compose.yml up -d

FROM ubuntu:24.04

ARG py_version=python3.11
ARG gustavo_version=0.3.12

LABEL version=${gustavo_version}
LABEL maintainer="paritosh.ramanan@okstate.edu"

RUN apt-get -y update && apt-get -y upgrade

RUN apt-get -y install build-essential supervisor software-properties-common

RUN add-apt-repository ppa:deadsnakes/ppa

RUN apt-get -y install python3-pip ${py_version} ${py_version}-venv ${py_version}-dev

RUN ${py_version} -m venv /opt/venv

ENV PATH="/opt/venv/bin:$PATH"

RUN pip3 install colorlog==6.9.0

RUN pip3 install --extra-index-url https://pypi.fury.io/osu-home-stri/ gustavo==${gustavo_version}

#CMD ["gustavo", "gui", "-p", "8154"]
