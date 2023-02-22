# Worker Preprocessing

The Worker serves as the bookkeeper at each edge device. This document describes the varied steps that are useful in setting up the worker node at the edge level.

## Preprocessing Steps

### Prepare Worker machine

1. Install docker on the Worker if not already present using the steps outlined [here](https://docs.docker.com/get-docker/). 
2. Ensure non root privilege access to docker by following the guidelines mentioned [here](https://docs.docker.com/engine/install/linux-postinstall/). 
3. Ensure non root privileges on `/home/ubuntu/.docker/config.json` by executing the command  `sudo chmod 777 /home/ubuntu/.docker/config.json`
4. If docker is already installed on the machine, you need to check if there are containers already running. You can do this using `docker ps`
5. If you need to wipe out all containers on the machine, please run the following two commands `docker stop $(docker ps -a -q)` and `docker rm $(docker ps -a -q)`
6. Ensure that docker clients can talk to local registries by creating a file `/etc/docker/daemon.json`. Open and edit the file as follows: 
    ```{  "insecure-registries":["MANAGER_HOST:MANAGER_PORT"]}```
    
    **Remember: `MANAGER_HOST:MANAGER_PORT` must match the corresponding entries in `worker.env`**
