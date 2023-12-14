FROM python:3.10

WORKDIR /app
COPY . .
# RUN DEBIAN_FRONTEND="noninteractive"
# Installing prerequisite packages
RUN apt-get update && apt-get install -y tzdata
RUN apt-get -y install curl unzip groff less

EXPOSE 8000

RUN chmod 755 ./scripts/*
RUN chmod +x ./scripts/start-celerybeat.sh
RUN chmod +x ./scripts/start-celeryworker.sh
RUN chmod +x ./scripts/start-flower.sh
RUN chmod +x ./scripts/start-setup.sh
RUN chmod +x ./scripts/start-app.sh

RUN ./scripts/start-setup.sh

CMD ["/bin/bash", "./scripts/start-app.sh"]