## Platform Management

Before we discuss how to orchestrate containers across edge devices, it is important to understand the difference between an App, Container Image and a Container.

* **Application (App)**: A configuration or a set of parameters that govern the execution of the computation on the edge provided in **.yaml** format.
* **Image**: A ***static*** container image that encapsulates code and all the libraries. This is the image that is present on say Docker Hub.
* **Container**: An image that is ***currently running on a device***!. 

**Remember the following key differences:**

1. An **App** (i.e. a set of parameters/configurations/settings governing your code) is what you register with Gustavo ***so that your container image can run correctly***.
2. An **Image** is a container image that is not yet running but has been built and stored somewhere. ***For instance, all the images currently on Docker Hub***.
3. A **Container** is an image that is currently running.

### Let us take a look at what a typical Gustavo app looks like 
We consider a simple linear regression model that we wish to run across a bunch of devices. Here is an example of an App named **test_linreg** contained in **test_linreg.yaml**
``` 
    #(REQUIRED): name of the app
    test_linreg: 
    
        #(REQUIRED): The image that this app is associated with
        docker_image: "REGISTRY_IP:REGISTRY_PORT/test_linreg"
        
        #(OPTIONAL): any environment variables necessary for running the underlying code 
        env_vars:
            CACHE: "64"
            NETRESTRICT: "0.0.0.0/0"
       
        #(OPTIONAL): A volume mapping scheme to indicate the set of "host" directories to be mounted inside the container and vice-versa.
        volumes:
          - "/tmp/:/tmp/1"
          - "/var/tmp/:/var/tmp/1:rw"
        
        #(OPTIONAL): Ports that might be needed by the underlying code.
        starting_ports:
          - 9000: 9000
          - 30303: 30303
        
        #Some other under the hood values that are required but need not be changed.
        running: True
        networks:
            - "nebula"
        rolling_restart: True
        containers_per:
            server: 1
        privileged: False
        devices: []
```

### App Creation
In order to deploy applications, we must first create a application configuration file. In this example we are going to be using `test_linreg.yml` to deploy a sample linear regression app.

#### test_linreg configuration file: `test_linreg.yml`

First we take `test_linreg.yml` that looks something like this: 
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
    
Ensure that all entries including REGISTRY_IP and REGISTRY_PORT are changed. Nothing else needs to be changed here

Lets look at how to create a sample application contained in the container image `test_linreg`

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

**Congratulations! You have just created your first app**

### Update an already created app
Edit `test_linreg.yml` and change necessary parameters. For instance, say I want to change an environment variable CACHE to 1064.
``` 
    test_linreg:
        docker_image: "172.31.17.1:5000/test_linreg"
        env_vars:
            #for instance, say I want to change an environment variable
            CACHE: "1064"
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

Run `gustavo apps update -n test_linreg -f test_linreg.yml` to update the app. 

Similarly, you can also update the ***images associated with your app***. Edit the file as follows:
``` 
    test_linreg:
        #NOTICE how the image name has been changed here
        docker_image: "172.31.17.1:5000/test_multiple_linreg"
        env_vars:
            #for instance, say I want to change an environment variable
            CACHE: "1064"
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
Now again run `gustavo apps update -n test_linreg -f test_linreg.yml` to update the app.

### Delete an app

Deletion is simple. Just execute the command `gustavo apps delete -n <app_name>`. For instance, if you want to delete the app `test_linreg`
run the command `gustavo apps delete -n test_linreg`

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
