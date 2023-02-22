# Tear down manager

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
