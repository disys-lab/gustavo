# Gustavo
Gustavo is a container orchestration framework constructed for Demo A3 under Research Thrust 2 of [NASA HOME STRI Project](https://homestri.ucdavis.edu/research). 
Gustavo is designed to be a one stop shop for administering applications in an **autonomous, self aware** fashion.
Gustavo is available in a Command Line Interface and can be run on Linux/Mac Environments as well as under Windows with the help of Windows Subsystem for Linux (WSL).
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

```gustavo apps -n test_linreg -f sample.yaml```

The following files are essential:
   - The environment file contains the list of environment variables needed for running the manager and its allied services.
     A sample ```manager.env``` file is as follows:
```
        REGISTRY_HOST=127.0.0.1
        REGISTRY_PORT=5000
          
        DREGSY_CONFIG_FILE_PATH=./.config/gustavo/dregsy_conf.yml
        DREGSY_MAPPING_FILE_PATH=./.config/gustavo/mappings_list.yml
        
        REDIS_HOST=127.0.0.1
        REDIS_PORT=6379
        REDIS_AUTH_TOKEN="teentakle1212"
        
        MANAGER_HOST=127.0.0.1
        MANAGER_PORT=80
        
        MONGO_HOST=127.0.0.1
        MONGO_PORT=27017
        MONGO_USERNAME=nebula
        MONGO_PASSWORD=nebula
        MONGO_CERTIFICATE_FOLDER_PATH=/tmp/
        
        NEBULA_USERNAME=nebula
        NEBULA_PASSWORD=nebula
        NEBULA_AUTH_TOKEN="teentakle1212"
```
  - ```dregsy_conf.yml``` contains configuration for dregsy. Needs to be edited according to .env file.
  - ```mappings_list.yml``` contains which images to sync. This file is dynamically read. Feel free to change the entries during run time to pause or start sync of new/existing images.

The docker daemon requires registries to be running ```http```. However, the current version only supports ```http```. To turn off ```https```, follow the steps outlined in the [link](https://docs.docker.com/registry/insecure/)
This needs to be done at each host where a docker daemon might be running. Be careful to set the ```myregistrydomain:5000``` to the ```REGISTRY_HOST:REGISTRY_PORT```.


## Common Gotchas
If using podman, you must login using ```podman login docker.io``` prior to launching this tool. Else there will be authentication errors.

## Development and Maintenance
Gustavo was conceived and developed by researchers at Oklahoma State University and Georgia Tech.

* [Paritosh Ramanan](https://ceat.okstate.edu/iem/people/ramanan-faculty-profile.html)
* [Nagi Gebraeel](https://www.isye.gatech.edu/users/nagi-gebraeel)

## Documentation

To run documentation using ```pdoc3```, run
```
pdoc3 -o ../docs-internal/ --html .
```

#For pdf version
First run ```pdoc3```, then you can run for eg:

```pdoc3 -o <location> --pdf gustavo.md > <location>/gustavo.md```

Add to the top of .md file 
```
---
mainfont: DejaVuSerif.ttf
sansfont: DejaVuSans.ttf
monofont: DejaVuSansMono.ttf 
mathfont: texgyredejavu-math.otf 
---
```

To run pandoc:
```
pandoc --metadata=title:"Project Gustavo: A nifty CLI to orchestrate container images in a distributed manner" --from=markdown+abbreviations+tex_math_single_backslash --pdf-engine=xelatex --variable=mainfont:"DejaVuSerif.ttf" --toc --toc-depth=4 --output=gustavo.pdf  <location>/gustavo.md
```
