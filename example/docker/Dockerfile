FROM python:3.6-stretch

ENV DB_ENV live
ENV TERM xterm
ENV LC_ALL C.UTF-8
ENV TZ=America/Los_Angeles


#################################################################
# Install

RUN ln -snf /usr/share/zoneinfo/$TZ /etc/localtime && \
    echo $TZ > /etc/timezone && \
    echo 'alias ll="ls -alg"' >> ~/.bashrc


RUN apt-get update && \
    apt-get install -y \
    supervisor \
    nano \
    wget \
    curl && \
    rm -rf /var/lib/apt/lists/*


COPY docker/requirements.txt /requirements.txt
RUN pip install -r /requirements.txt  && \
    pip freeze


#################################################################
# Make folders

RUN mkdir -p /var/www/app/ && \
    chown -R www-data:www-data /var/www/app/


#################################################################
# Container settings

WORKDIR /var/www/app/
EXPOSE 5000

#################################################################

#################################################################
# Copy app files. Should be at the end to improve build speed.

COPY . /var/www/app

ENTRYPOINT ["python", "-u"]
CMD ["/var/www/app/app.py"]

#################################################################


