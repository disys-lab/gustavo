# Manager Setup

The Manager serves as the entry point into the entire platform. This document describes the varied steps that are useful in setting up the manager node.

## Preprocessing Steps

#### test_linreg configuration file: `test_linreg.yml`

1. The test app configuration is present in the file `test_linreg.yml`. It should look somewhat like this:
    
``` 
    test_linreg:
        docker_image: "172.31.17.1:5000/test_linreg"
        env_vars:
            CACHE: "64"
            NETRESTRICT: "0.0.0.0/0"
        networks:
            - "nebula"
        volumes:
          - "/tmp/:/tmp/1"
          - "/var/tmp/:/var/tmp/1:rw"
        starting_ports:
          - 9000: 9000
          - 30303: 30303
        running: True
        rolling_restart: True
        containers_per:
            server: 1
        privileged: False
        devices: []
```
    
    **Remember: Dont give container tags while listing the docker_image, just specify the name of the container.**
    
2. Ensure that all entries including REGISTRY_IP and REGISTRY_PORT are changed. Nothing else needs to be changed here

## Setup

### Bring up Manager services

1.    First set the environment variable `GUSTAVO_CONFIG_FILE` pointing to the location of `manager.env` using `export GUSTAVO_CONFIG_FILE=/path/to/manager.env` 
    
      For instance, if your file is located at say `/home/ubuntu/demo/`, then your export command must look like `export GUSTAVO_CONFIG_FILE=/home/ubuntu/demo/manager.env`
    
2.    Now run `gustavo manager up` . You should see something like this :

```
       nebula@172.31.17.1:80
       DOCKER_HOST:unix:/var/run/docker.sock
       2: Pulling from library/registry
       Digest: sha256:dc3cdf6d35677b54288fe9f04c34f59e85463ea7510c2a9703195b63187a7487
       Status: Image is up to date for registry:2
       docker.io/library/registry:2
       Registry Up
       Using default tag: latest
       latest: Pulling from homert2admin/redis
       Digest: sha256:c2cbe8a592927bb74033f9c29b103ebc8e1ab3ed9598a9e937aaa2a723d5b8a7
       Status: Image is up to date for homert2admin/redis:latest
       docker.io/homert2admin/redis:latest
       Redis Up
       latest: Pulling from homert2admin/dregsy
       Digest: sha256:1900a8aa72436218c9913ee07c122676d2a354350a21f1392c73cea594f37e66
       Status: Image is up to date for homert2admin/dregsy:latest
       docker.io/homert2admin/dregsy:latest
       Syncer Up
       4.0.1: Pulling from library/mongo
       Digest: sha256:acf40597af1cc8bc3bf9a3f1aea87222abca1a99911febd28277ca8f0c142177
       Status: Image is up to date for mongo:4.0.1
       docker.io/library/mongo:4.0.1
       Mongo Up
       2.6.1: Pulling from nebulaorchestrator/manager
       Digest: sha256:b531a4bdabc9404cddc96d2d1b1babe6826e8aebce955049c9380f84814593e2
       Status: Image is up to date for nebulaorchestrator/manager:2.6.1
       docker.io/nebulaorchestrator/manager:2.6.1
       Manager Up
       Waiting for manager to come alive..
       Manager Up
      
```
    
The output logs could be different from the one shown above and might take time a few minutes especially if this is being run for the first time. But you have to make sure these lines appear:
    
    Registry Up
    
    Redis Up
    
    Syncer Up
    
    Mongo Up
    
    Manager Up
    
    Waiting for manager to come alive..
    
    Manager Up
    
    Once the command exits 
    
3. Run `docker ps` to check if all the containers have been brought up. Your output must look something like this:
    
``` 
    bddf795d4068        nebulaorchestrator/manager:2.6.1   "gunicorn --config /…"   8 seconds ago       Up 7 seconds        0.0.0.0:80->80/tcp         manager
    0b86865cf339        mongo:4.0.1                        "docker-entrypoint.s…"   10 seconds ago      Up 8 seconds        0.0.0.0:27017->27017/tcp   mongo
    1525094c68b9        homert2admin/dregsy:latest         "dregsy -config=conf…"   10 seconds ago      Up 9 seconds                                   syncer
    92c624de42f1        homert2admin/redis                 "docker-entrypoint.s…"   11 seconds ago      Up 10 seconds       0.0.0.0:6379->6379/tcp     redis
    453e54ed08b3        registry:2                         "/entrypoint.sh /etc…"   12 seconds ago      Up 11 seconds       0.0.0.0:5000->5000/tcp     registry
```
    
4. Check if the registry is populated by running `gustavo registry list`. You should get an output like this:
    
``` 
    nebula@172.31.17.1:80
    DOCKER_HOST:unix:/var/run/docker.sock
    {'repositories': ['test_linreg']}
```
    

## Platform Management and handling

Lets look at how to deploy a sample application contained in the container image `test_linreg`

### Bring up the `test_linreg`

Execute the command 

`gustavo apps create -n test_linreg -f test_linreg.yml`

You should see something like:

``` 
nebula@172.31.17.1:80
DOCKER_HOST:unix:/var/run/docker.sock
{'name': 'test_linreg', 'tags': ['latest']}
test_linreg:latest have been found in local registry
created nebula app : test_linreg
created nebula device_group : bca
```

### Check status and pulse of Edge Nodes

You can do a variety of checks using the `gustavo cache [OPTION]` to check status of containers as well as vitals and device groups:

``` 
Usage: gustavo cache [OPTIONS] COMMAND [ARGS]...

  obtain status of various workers on the platform

Options:
  --version  Show the version and exit.
  --help     Show this message and exit.

Commands:
  containers  check container images on host and device_groups
  hosts       fetch all hosts
  vitals      acquire vitals for devices
```

## Tear down manager

Tearing down the manager comprises of two sequential parts:

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

### Manager removal

Run the command `gustavo manager remove` and answer `y` to every prompt. The tool will systematically tear down all services.

Alternately, you can even selectively bring down services using the command `gustavo manager remove -s <service_name>`

For example, `gustavo manager remove -s mongo` will only remove mongo.

In addition for advanced debugging, you can also perform the following commands with the manager option:

``` 

Usage: gustavo manager [OPTIONS] COMMAND [ARGS]...

Commands:
check    check manager services
kill     kill manager services
remove   remove manager services
restart  restart manager services
start    start manager services
stop     stop manager services
up       bring up manager services
```

## Troubleshooting Common Errors

### `GUSTAVO_CONFIG_FILE not defined`

Check to make sure that [Step 1 of Setup](https://www.notion.so/Manager-Setup-39ab45e7218d49abb032ea75c89dd9e1) is complete. You can check if the environment variable `GUSTAVO_CONFIG_FILE` is set by running `echo $GUSTAVO_CONFIG_FILE`

### Container already in use error

If you get the error:

`"Conflict. The container name "/<container_name>" is already in use by container "<container_id>". You have to remove (or rename) that container to be able to reuse that name."`

Remove the container

`gustavo manager remove -s <container_name>`

Restart the container

`gustavo manager up -s <container_name>`

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