# Tear Down Worker

## Bring down the sample app

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

## On each Edge Node

**On each Edge Node**, execute the command `gustavo worker remove`. Your should get a confirmation that looks like `Worker named: worker_bca has been brought down`

Bear in mind that you can always use `-n <worker_name>` in case you did not stick to the defaults provided by our platform.

## Troubleshooting Common Errors

### `GUSTAVO_CONFIG_FILE not defined`

Check to make sure that [Step 1 of Setup](https://www.notion.so/Worker-Setup-1f21267b78074e1a92f230b14c018e90) is complete. You can check if the environment variable `GUSTAVO_CONFIG_FILE` is set by running `echo $GUSTAVO_CONFIG_FILE`

### Container already in use error

If you get the error:

`"Conflict. The container name "/<container_name>" is already in use by container "<container_id>". You have to remove (or rename) that container to be able to reuse that name."`

Remove the container

`gustavo worker remove -n <container_name>`

Restart the container

`gustavo worker up -n <container_name>`

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