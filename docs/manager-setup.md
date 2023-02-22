# Manager Setup

## Bring up Manager services

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