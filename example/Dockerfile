FROM alpine:3.6

# Install our basic requirements.
RUN apk add --no-cache python3 python3-dev musl-dev gcc
RUN pip3 install Flask_SocketIO

# Install the specified async library, supported values are "eventlet", "gevent" or "none".
ARG ASYNC_LIB="none"
RUN if [ "${ASYNC_LIB}" == "eventlet" ]; then \
      pip3 install eventlet; \
    elif [ "${ASYNC_LIB}" == "gevent" ]; then \
      pip3 install gevent gevent-websocket; \
    elif [ "${ASYNC_LIB}" == "none" ]; then \
      true; \
    else \
      echo "ERROR!! Unknown value of ASYNC_LIB: ${ASYNC_LIB}"; \
      false; \
    fi

# Add a user to run as, with the specified user and group ids.
ARG PUID=1225
ARG PGID=1225
RUN addgroup -g ${PGID} demo && \
    adduser -D -u ${PUID} -G demo demo
USER demo

# Copy in the application code.
COPY . /demoapp
WORKDIR /demoapp

# Define the entrypoint and port, we must specify the flask app by environment variable.
ENV FLASK_APP="app.py"
ENTRYPOINT ["flask", "run", "-h", "0.0.0.0", "-p", "5000"]
EXPOSE 5000
