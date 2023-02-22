# Worker Setup

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

## Setup

### On each Worker

1. First set the environment variable `GUSTAVO_CONFIG_FILE` pointing to the location of `worker.env` using `export GUSTAVO_CONFIG_FILE=/path/to/worker.env` 
    
    For instance, if your file is located at say `/home/ubuntu/demo/`, then your export command must look like `export GUSTAVO_CONFIG_FILE=//home/ubuntu/demo/worker.env`
    
2. Now run `gustavo worker up`. You should see something like this :
    
```
    latest: Pulling from homert2admin/worker
    Digest: sha256:16cb0f765ace8e77c564f994f0a0e2f9c56c61a94349536a9a21be47a0be1587
    Status: Image is up to date for homert2admin/worker:latest
    docker.io/homert2admin/worker:latest
    nebula@172.31.17.1:80
    DOCKER_HOST:unix:/var/run/docker.sock
    Worker Up
```
    
The output logs could be different from the one shown above and might take time a few minutes especially if this is being run for the first time. But you have to make sure these lines appear:

Worker Up

Once the command exits 
    
3. Run `docker ps` to check if all the containers have been brought up. Your output must look something like this:
    
```
    CONTAINER ID        IMAGE                        COMMAND                  CREATED             STATUS              PORTS               NAMES
    2ae898881fea        homert2admin/worker:latest   "python /worker/work…"   4 seconds ago       Up 3 seconds                            worker_bca
```
    

## Tear down worker

### Bring down the sample app

Next, on BGN, delete `test_linreg` is deleted using `gustavo apps delete -n test_linreg`.

You should get an output which looks like:

```
nebula@172.31.17.1:80
DOCKER_HOST:unix:/var/run/docker.sock
About to delete test_linreg, do you want to continue? [y/N]: y
checked nebula app list for : bca
updated nebula device_group : bca
Deleted test_linreg from device group
deleted nebula app : test_linreg
Deleted test_linreg
```

This only needs to be done from the BGN.

### On each BEN

**On each BEN**, execute the command `gustavo worker remove`. Your should get a confirmation that looks like `Worker named: worker_bca has been brought down`

Bear in mind that you can always use `-n <worker_name>` in case you did not stick to the defaults provided by our platform.

## Troubleshooting Common Errors

### `GUSTAVO_CONFIG_FILE not defined`

Check to make sure that [Step 1 of Setup](https://www.notion.so/Worker-Setup-1f21267b78074e1a92f230b14c018e90) is complete. You can check if the environment variable `GUSTAVO_CONFIG_FILE` is set by running `echo $GUSTAVO_CONFIG_FILE`

### Container already in use error

If you get the error:

`"Conflict. The container name "/<container_name>" is already in use by container "<container_id>". You have to remove (or rename) that container to be able to reuse that name."`

Remove the container

`gustavo worker remove -n <container_name>`

Restart the container

`gustavo worker up -n <container_name>`

### Address already in use error

`Error starting userland proxy: listen TCP <ip>:<port>: bind: address already in use"`

Then do the following steps on linux:

`sudo lsof -i -P -n | grep <port>`

Locate the process ID that are on `LISTEN` status on `<port>` 

Kill those processes with `sudo kill 18930`

For example:

```
sudo lsof -i -P -n | grep 80
apache2   18930            root    4u  IPv6 823738609      0t0  TCP *:80 (LISTEN)
apache2   18933        www-data    4u  IPv6 823738609      0t0  TCP *:80 (LISTEN)
apache2   18934        www-data    4u  IPv6 823738609      0t0  TCP *:80 (LISTEN)

sudo kill 18930
```