# Troubleshooting Common Errors

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