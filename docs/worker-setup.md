# Worker Setup

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