## Platform Management and handling

In order to deploy applications, we must first create a application configuration file. In this example we are going to be using `test_linreg.yml` to deploy a sample linear regression app.

### test_linreg configuration file: `test_linreg.yml`

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
