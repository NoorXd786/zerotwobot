Stdout
FROM python:3.11.2-slim-buster

WORKDIR /zerotwobot/

RUN apt-get update && apt-get upgrade -y
RUN apt-get -y install git
RUN python3.11 -m pip install -U pip
RUN apt-get install -y wget python3-pip curl bash neofetch ffmpeg software-properties-common
RUN apt-get install -y --no-install-recommends ffmpeg

COPY requirements.txt .

RUN pip3 install wheel
RUN pip3 install --no-cache-dir -U -r requirements.txt

COPY . .
CMD ["python3.11", "-m", "zerotwobot"]
