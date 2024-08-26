import redis, click, pickle, sys
from .NebulaBase import NebulaBase

"""
CAUTION: This module relies on the Redis in memory data store with expiry of cache enabled.
The code will work for small cases but might break at scale. This needs to be fixed.
Right now this is a hot fix style code that needs to be re-written elgantly.
"""


class ErrorHandling(Exception):
    pass


class Cache(NebulaBase):

    """
    This module relies on the Redis in memory data store with expiry of cache enabled.

    """

    def __init__(
        self,
    ):
        """
        Inorder to make Cache rest friendly replaced sys.exit() with raising exceptions which will get excepted
        in gustavo.py and eventually return a dictionary there {"error": True, "response": reason for error}
        """

        click.echo(
            click.style(
                "WARNING:This is an experimental feature and is not optimized for scale. Results might vary.",
                fg="red",
            )
        )
        NebulaBase.__init__(self)
        try:
            click.echo(
                click.style("CACHE_PREFIX:" + str(self.CACHE_PREFIX), fg="yellow")
            )
            self.redisObj = redis.StrictRedis(
                host=self.REDIS_IP, port=self.REDIS_PORT, password=self.REDIS_AUTH_TOKEN
            )
        except Exception as e:
            click.echo(click.style(e, fg="red"))
            # sys.exit()
            raise ErrorHandling

    def keyPartition(self, raw_key):
        """
        Partitions key based on the delimiter "_"

        Parameters
        ----------
        raw_key : string
            Raw key to be partitioned

        Returns
        -------

        component_tuple : list
            A tuple of three key components

        """
        key = str(raw_key).replace("'", "")
        key_components = str(key).split("_")
        return key_components[0], key_components[1], key_components[2]

    def scanLatest(
        self,
    ):

        """
        Iteratively scan and find the latest matching key and return the most freshest key

        Returns
        -------
        host_dict : dict
            A dictionary containing the latest key value pairs
        """

        host_dict = {}

        for key in self.redisObj.scan_iter(self.CACHE_PREFIX + "_*"):
            prefix, timestamp, host = self.keyPartition(key)
            if host not in host_dict.keys():
                host_dict[host] = timestamp
            else:
                if host_dict[host] < timestamp:
                    host_dict[host] = timestamp
        return host_dict

    def getHostDeviceGroupFromKey(self, host_id):
        """
        Obtain the device group from the given key

        Parameters
        ----------

        host_id : string
            The key value to check

        Returns
        -------

        host : string
            host part of the key

        device_group : string
            device group part of the key

        """
        device_group = host_id.split("@")[0]
        host = host_id.split("@")[1]
        return host, device_group

    def getHosts(self, device_group_queried, host_queried):

        """
        Determines which hosts and device groups currently exist in the cache by querying Redis.

        Parameters
        ----------
        device_group_queried : string
            The device group being queried

        host_queried : string
            The host being queried

        Returns
        -------
        mapping_dict : dict
            A dict containing {
                                "host_queried":the query results for the host,
                                "device_group_queried":the query results for the device group,
                                "response":a boolean value depending on success of query
                              }


        """

        host_dict = {}
        device_group_dict = {}
        for key in self.redisObj.scan_iter(self.CACHE_PREFIX + "_*"):
            prefix, timestamp, host_id = self.keyPartition(key)
            host, device_group = self.getHostDeviceGroupFromKey(host_id=host_id)
            if host not in host_dict.keys():
                host_dict[host] = [device_group]
            else:
                host_dict[host] = host_dict[host] + [device_group]

            if device_group not in device_group_dict.keys():
                device_group_dict[device_group] = [device_group]
            else:
                device_group_dict[device_group] = device_group_dict[device_group] + [
                    device_group
                ]

        if host_queried == "all" and device_group_queried == "all":
            response = host_dict

        elif host_queried == "all" and device_group_queried != "all":
            if device_group_queried in device_group_dict.keys():
                response = device_group_dict[device_group_queried]
            else:
                response = []

        elif host_queried != "all" and device_group_queried == "all":
            if host_queried in host_dict:
                # print(host_dict[host_queried])
                response = host_dict[host_queried]
            else:
                response = []

        else:
            if (
                host_queried in host_dict.keys()
                and device_group_queried in host_dict[host_queried]
            ):
                # print(True)
                response = True
            else:
                # print(False)
                response = False

        return {
            "host_queried": host_queried,
            "device_group_queried": device_group_queried,
            "response": response,
        }

    def unpickleData(self, device_group, host):

        """
        Given a device group and host, unpickles the query result (vitals and containers) from Redis cache.

        Parameters
        ----------
        device_group: string
            The device group being queried

        host : string
            The host being queried

        Returns
        -------
        mapping_dict : dict
            A dict containing {
                                "host_queried":the query results for the host,
                                "device_group_queried":the query results for the device group,
                                "response":a boolean value depending on success of query
                              }

        key : string
            The key that led to the match

        """

        key = str(device_group + "@" + host)
        host_dict = self.scanLatest()
        # response = {"host_queried": host, "device_group_queried": device_group, "response": response}
        if key in host_dict.keys():
            timestamp = host_dict[key]
            try:
                dataObj = self.redisObj.get(
                    self.CACHE_PREFIX + "_" + timestamp + "_" + key
                )
                data_dict = pickle.loads(dataObj)
                return {
                    "host_queried": host,
                    "device_group_queried": device_group,
                    "response": data_dict,
                }, key
            except Exception as e:
                click.echo(click.style(e, fg="red"))
                return {
                    "host_queried": host,
                    "device_group_queried": device_group,
                    "response": {},
                }, key
        else:
            click.echo(
                click.style("{} not found in cache reports".format(key), fg="red")
            )
            return {
                "host_queried": host,
                "device_group_queried": device_group,
                "response": {},
            }, key

    def getIndividualVitals(self, device_group, host):
        """
        Fetches the vitals across device groups and host combinations
        Parameters
        ----------
        device_group: string
            The device group being queried

        host : string
            The host being queried

        TODO: REST-fy this function, currently executes sys.exit()

        Inorder to make Cache rest friendly replaced sys.exit() with raising exceptions which will get excepted
        in getAssetsForAll(self,asset,device_group_id="all",host_id="all") and eventually return a dictionary there
        {"error": True, "response": reason for error}

        """
        response, key = self.unpickleData(device_group, host)
        data_dict = response["response"]
        if bool(data_dict):
            try:
                mem = str(data_dict["memory_usage"])
                disk = str(data_dict["root_disk_usage"])
                cpu_core_use = str(data_dict["cpu_usage"]["cores"])
                cpu_pct_use = str(data_dict["cpu_usage"]["used_percent"])
                time = str(data_dict["report_creation_time"])
                click.echo(
                    click.style(
                        key
                        + "at time:"
                        + time
                        + "\t mem:"
                        + mem
                        + "\t"
                        + "disk:"
                        + disk
                        + "\t"
                        + "cpu_cores:"
                        + cpu_core_use
                        + "\t"
                        + "cpu_percent:"
                        + cpu_pct_use,
                        fg="blue",
                    )
                )
                return {
                    "error": False,
                    "response": key
                    + "at time:"
                    + time
                    + "\t mem:"
                    + mem
                    + "\t"
                    + "disk:"
                    + disk
                    + "\t"
                    + "cpu_cores:"
                    + cpu_core_use
                    + "\t"
                    + "cpu_percent:"
                    + cpu_pct_use,
                }

            except Exception as e:
                click.echo(click.style(e, fg="red"))
                # sys.exit()
                raise ErrorHandling
        else:
            click.echo(click.style("No key matches {}".format(key), fg="red"))
            return {"error": True, "response": "no key matches {}".format(key)}

    def getIndividualContainers(self, device_group, host):
        """
        Fetches the containers for device group and host combination
        Parameters
        ----------
        device_group: string
            The device group being queried

        host : string
            The host being queried

        TODO: REST-fy this function, currently executes sys.exit()

        Inorder to make Cache rest friendly replaced sys.exit() with raising exceptions which will get excepted
        in getAssetsForAll(self,asset,device_group_id="all",host_id="all") and eventually return a dictionary there
        {"error": True, "response": reason for error}
        """

        response, key = self.unpickleData(device_group, host)
        data_dict = response["response"]
        if bool(data_dict):
            try:
                containers = str(data_dict["apps_containers"])
                time = str(data_dict["report_creation_time"])
                click.echo(
                    click.style(
                        key + " at time:" + time + " containers:" + str(containers),
                        fg="blue",
                    )
                )
                return {
                    "error": False,
                    "response": key
                    + " at time:"
                    + time
                    + " containers:"
                    + str(containers),
                }
            except Exception as e:
                click.echo(click.style(e, fg="red"))
                # sys.exit()
                raise ErrorHandling
        else:
            click.echo(click.style("No key matches {}".format(key), fg="red"))
            return {"error": True, "response": "no key matches {}".format(key)}

    # not optimized at all

    def getAssetsForAll(self, asset, device_group_id="all", host_id="all"):
        """
        TODO: This function hasnt been implemented completely yet. Need to find an efficient way for querying at scale.
        """
        if device_group_id != "all" and host_id != "all":
            if asset == "vitals":
                try:
                    responseVitals = self.getIndividualVitals(device_group_id, host_id)
                except ErrorHandling:
                    return {
                        "error": True,
                        "response": "some problem with gathering vitals",
                    }
                except Exception as e:
                    return {"error": True, "response": e}
                return {"error": False, "response": responseVitals}
            elif asset == "containers":
                try:
                    responseContainers = self.getIndividualContainers(
                        device_group_id, host_id
                    )
                except ErrorHandling:
                    return {"error": True, "response": "some problem with containers"}
                except Exception as e:
                    return {"error": True, "response": e}
                return {"error": False, "response": responseContainers}

        host_dict = self.scanLatest()

        if len(host_dict.keys()) == 0:
            click.echo(
                click.style(
                    "No data matches the query device_group:{},hosts:{}".format(
                        device_group_id, host_id
                    ),
                    fg="red",
                )
            )
            return {
                "error": False,
                "response": "No data matches the query device_group:{},hosts:{}".format(
                    device_group_id, host_id
                ),
            }

        for host in host_dict.keys():
            device_group = host.split("@")[0]
            host = host.split("@")[1]
            fetch = False
            if device_group_id != "all" and device_group == device_group_id:
                fetch = True
            elif host_id != "all" and host == host_id:
                fetch = True
            elif host_id == "all" and device_group_id == "all":
                fetch = True

            if fetch:
                if asset == "vitals":
                    try:
                        responseVitals = self.getIndividualVitals(device_group, host)
                    except ErrorHandling:
                        return {
                            "error": True,
                            "response": "some problem with gathering vitals",
                        }
                    except Exception as e:
                        return {"error": True, "response": e}
                    return {"error": False, "response": responseVitals}
                elif asset == "containers":
                    try:
                        responseContainers = self.getIndividualContainers(
                            device_group, host
                        )
                    except ErrorHandling:
                        return {
                            "error": True,
                            "response": "some problem with containers",
                        }
                    except Exception as e:
                        return {"error": True, "response": e}
                    return {"error": False, "response": responseContainers}

        # return
