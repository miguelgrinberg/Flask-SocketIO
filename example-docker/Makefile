.DEFAULT_GOAL := default

build:
	docker build -t socketio .

start:
	docker run -d -p 5000:5000 --name socketio socketio

	@echo "\n\n====> Log into the container with: \n docker exec -it socketio"
	@echo "====> Get container logs with with: \n docker logs socketio -f\n"

clean:
	-docker stop socketio
	-docker rm socketio

default: clean build start