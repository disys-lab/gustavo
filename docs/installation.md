# Installation

There are two ways to install Gustavo.

## Install Gustavo from Gemfury

Execute this command:

`pip install --index-url https://pypi.fury.io/osu-home-stri/ gustavo==0.1.4`

## (OPTIONAL) Install `gustavo`  directly from binaries.

Download the administration tool `gustavo` and copy it to a location the system path for example `/usr/bin`. You can also create a symbolic link located in `/usr/bin/`  using:

 `sudo ln -s path/to/gustavo /usr/bin/gustavo`

## Configure `gustavo`

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
    
2. Provide all the required config files for booting the worker. There are three files needed to configure the manager:
    1. `worker.env`: A list of configurations for the worker to interact with the manager that has been hosted at the BGN 
3. The `worker.env` must look something like this:
    
```
    #the local registry details
    REGISTRY_HOST=172.31.17.1
    REGISTRY_PORT=5000
    
    #the details for Redis
    REDIS_HOST=172.31.17.1
    REDIS_PORT=6379
    REDIS_AUTH_TOKEN="teentakle1212"
    REDIS_EXPIRE_TIME=10
    REDIS_KEY_PREFIX="nebula-reports"
    
    #the details of the manager host and port
    MANAGER_HOST=172.31.17.1
    MANAGER_PORT=80
    
    #nebula details
    NEBULA_USERNAME=nebula
    NEBULA_PASSWORD=nebula
    NEBULA_AUTH_TOKEN=bmVidWxhOm5lYnVsYQ==
```
    
Change the relevant entries. Common entries to be changed would include the host and ports of the registry, redis, manager and the REDIS_AUTH_TOKEN.
    
