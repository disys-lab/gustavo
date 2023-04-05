# Installation

There are two ways to install Gustavo.

## Install Gustavo from Gemfury

Execute this command:

`pip install --index-url https://pypi.fury.io/osu-home-stri/ gustavo==0.1.4`

## Install `gustavo`  directly from binaries.

Download the administration tool `gustavo` and copy it to a location the system path for example `/usr/bin`. You can also create a symbolic link located in `/usr/bin/`  using:

 `sudo ln -s path/to/gustavo /usr/bin/gustavo`

## Install `gustavo`  directly from github.

Clone the Github repository `https://github.com/paritoshpr/gustavo.git` 

 `cd gustavo && sh builder.sh`

This will create a binary in `./gustavo/dist/<operating_system_name>/gustavo`.

Add this path to `~/.bashrc` to directly execute the binary.

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