# Manager Preprocessing

### Prepare Manager machine

1. Install docker on Manager if not already present using the steps outlined [here](https://docs.docker.com/get-docker/). 
2. Ensure non root privilege access to docker by following the guidelines mentioned [here](https://docs.docker.com/engine/install/linux-postinstall/). 
3. Ensure non root privileges on `/home/ubuntu/.docker/config.json` by executing the command  `sudo chmod 777 /home/ubuntu/.docker/config.json`
4. If docker is already installed on the machine, you need to check if there are containers already running. You can do this using `docker ps`
5. If you need to wipe out all containers on the machine, please run the following two commands `docker stop $(docker ps -a -q)` and `docker rm $(docker ps -a -q)`

### Prepare Gustavo
    
1. Check whether it is functional by either running: `gustavo --help` or `gustavo --version` . You must get something like this:
    
``` 
    Usage: gustavo [OPTIONS] COMMAND [ARGS]...
    
      Manage gustavo from a simple CLI.
    
    Options:
      --version  Show the version and exit.
      --help     Show this message and exit.
    
    Commands:
      apps          Manage applications
      cache         obtain status of various workers on the platform
      device-group  Manage device groups.
      manager       Administer the manager.
      ping          check nebula api responds
      prune         prune images.
      registry      Manage local registry.
      utils         utility commands
      worker        Manage worker.
```
    
2. Provide all the required config files for booting the manager. There are three files needed to configure the manager:
    1. `manager.env`: A list of configuration for the manager to be hosted at the BGN
    2. `dregsy_conf.yml`: To download container images from remote registries.
    3. `mappings_list.yml`: That provides a list of which remote images need to be downloaded.
    4. `test_linreg.yml` : A configuration of the test app that will be hosted at each edge node.
3. Ensure that docker clients can talk to local registries by creating a file `/etc/docker/daemon.json`. Open and edit the file as follows:
    
    ```{ "insecure-registries":["MANAGER_HOST:MANAGER_PORT"]}
    ```
    
    **Remember: `MANAGER_HOST:MANAGER_PORT` must match the corresponding entries in `manager.env`**
    

#### manager config file: `manager.env`

The `manager.env` must look like this:

``` 
#the local registry details
REGISTRY_HOST=172.31.17.1
REGISTRY_PORT=5000

#the syncer details: ie. location of the dregsy_conf.yml and mappings_list.yml
DREGSY_CONFIG_FILE_PATH=/home/ubuntu/workshop_demo/dregsy_conf.yml
DREGSY_MAPPING_FILE_PATH=/home/ubuntu/workshop_demo/mappings_list.yml

#the details for Redis
REDIS_HOST=172.31.17.1
REDIS_PORT=6379
REDIS_AUTH_TOKEN="teentakle1212"
REDIS_EXPIRE_TIME=10
REDIS_KEY_PREFIX="nebula-reports"

#the details of the manager host and port
MANAGER_HOST=172.31.17.1
MANAGER_PORT=80

#the details for MongoDb
MONGO_HOST=172.31.17.1
MONGO_PORT=27017
MONGO_USERNAME=nebula
MONGO_PASSWORD=nebula
MONGO_CERTIFICATE_FOLDER_PATH=/tmp/

#nebula details
NEBULA_USERNAME=nebula
NEBULA_PASSWORD=nebula
NEBULA_AUTH_TOKEN=bmVidWxhOm5lYnVsYQ==

#docker image details
REGISTRY_IMAGE="registry:2"
SYNCER_IMAGE="homert2admin/dregsy:latest"
REDIS_IMAGE="homert2admin/redis"
MONGO_IMAGE="mongo:4.0.1"
MANAGER_IMAGE="nebulaorchestrator/manager:2.6.1"

#network mode
MANAGER_NMODE="host"
WORKER_NMODE="host"
SYNCER_IMAGE="host"
```

Change the relevant entries. Common entries to be changed would include the host and ports of the registry, redis, manager and mongo, the REDIS_AUTH_TOKEN as well as the correct locations of the files: `dregsy_conf.yaml`, `mappings_list.yaml` as indicated by variables `DREGSY_CONFIG_FILE_PATH` and `DREGSY_MAPPING_FILE_PATH` respectively.

#### syncer config files: `dregsy_conf.yml`and `mappings_list.yml`

1. The file `dregsy_conf.yml` looks like this:

```
    # relay type, either 'skopeo' or 'docker'
    relay: skopeo
    # relay config sections
    skopeo:
      # path to the skopeo binary; defaults to 'skopeo', in which case it needs to
      # be in PATH
      binary: skopeo
      # directory under which to look for client certs & keys, as well as CA certs
      # (see note below)
      certs-dir: /etc/skopeo/certs.d
    docker:
      # Docker host to use as the relay
      dockerhost: unix:///var/run/docker.sock
      # Docker API version to use, defaults to 1.24
      api-version: 1.24
    
    # list of sync tasks
    tasks:
      - name: task1 # required
        # interval in seconds at which the task should be run; when omitted,
        # the task is only run once at start-up
        interval: 30
        # determines whether for this task, more verbose output should be
        # produced; defaults to false when omitted
        verbose: true
        # 'source' and 'target' are both required and describe the source and
        # target registries for this task:
        #  - 'registry' points to the server; required
        #  - 'auth' contains the base64 encoded credentials for the registry
        #    in JSON form {"username": "...", "password": "..."}
        #  - 'auth-refresh' specifies an interval for automatic retrieval of
        #    credentials; only for AWS ECR (see below)
        #  - 'skip-tls-verify' determines whether to skip TLS verification for the
        #    registry server (only for 'skopeo', see note below); defaults to false
        source:
          registry: registry.hub.docker.com
          auth: teentakle1212
        target:
          registry: 172.31.17.1:5000
          skip-tls-verify: true
        # 'mappings' is a list of 'from':'to' pairs that define mappings of image
        # paths in the source registry to paths in the destination; 'from' is
        # required, while 'to' can be dropped if the path should remain the same as
        # 'from'. Additionally, the tags being synced for a mapping can be limited
        # by providing a 'tags' list. When omitted, all image tags are synced.
        mappings_file: /mappings_list.yaml
```
        
There are two fields to pay attention to `auth` and `registry`. For auth, you can use the inbuilt utility in `gustavo utils syncer-auth-token` . Follow the prompts and provide the username and password and confirmation password for the remote registry. The password field will remain empty as you type. This is normal 
    
For example,  lets say the username is *johndoe123* and the password is *fountainhead* . Then the output is going to look like:

```
$ gustavo utils syncer-auth-token
Username: johndoe123   
Password: 
Repeat for confirmation:
```
    
After the confirmation is repeated it will lead to a long string being printed on the console:
    
`eyJ1c2VybmFtZSI6ICJqb2huZG9lMTIzIiwgInBhc3N3b3JkIjogImZvdW50YWluaGVhZCJ9`
    
Copy this string into the `auth` filed of `dregsy_conf.yml`
    
2. The file `mappings_list.yml` must look exactly like this:
    
``` 
    mappings:
          #generic images need to have library/ appended to their from tag
    
          - from: homert2admin/test_linreg
            to: test_linreg
            tags: ['latest']
```
    
We would be appending to this file quite a bit.