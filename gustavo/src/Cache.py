import redis, click, pickle, sys
from .NebulaBase import NebulaBase
from gustavo.pages.config.Logging import setup_logging
setup_logging()
import logging

"""
Reads cached worker vitals/container reports back out of Redis.

Reports themselves are written by the worker side (not this module) as
pickled blobs under keys shaped
``{CACHE_PREFIX}_{timestamp}_{device_group}@{host}``, with Redis's own
TTL expiring stale entries. This module only ever reads - it never
writes a cache entry itself.

CAUTION: relies on `SCAN`-ing the full key space (`scanLatest`,
`getHosts`) to find the latest report per host - works for small
deployments but doesn't scale to a large number of hosts/reports. Not
rewritten here, since fixing that is a real, separate change (e.g. a
secondary index instead of a full scan), not a docs pass.
"""


class ErrorHandling(Exception):
    """Raised for a Redis connection failure, or when data expected in a cached report is missing/malformed."""
    pass


class Cache(NebulaBase):
    """
    Reads cached worker vitals/container reports back out of Redis.

    Extends `NebulaBase` for its Redis connection attributes
    (`REDIS_IP`/`REDIS_PORT`/`REDIS_AUTH_TOKEN`/`CACHE_PREFIX`) - always
    constructed with `mode="CLI"` (see `__init__`), since the FastAPI
    backend's own monitoring path doesn't go through this class.

    Attributes
    ----------
    redisObj : redis.StrictRedis
        The Redis client used for every cache read.
    """

    def __init__(
        self,
        session_state=None,
    ):
        """
        Connect to Redis using connection details resolved via `NebulaBase.__init__`.

        Parameters
        ----------
        session_state : dict or None, optional
            Forwarded to `NebulaBase.__init__`. Since `Cache` always
            passes `mode="CLI"`, this is unused in practice - CLI mode
            reads connection details from `GUSTAVO_CONFIG_FILE` instead.

        Raises
        ------
        ErrorHandling
            If the Redis connection can't be established.

        Notes
        -----
        Originally called `sys.exit()` on a connection failure; replaced
        with raising a real exception so a REST caller (`gustavo.py`)
        can catch it and return ``{"error": True, "response": <reason>}``
        instead of killing the process.
        """
        logging.error(f"WARNING: This is an experimental feature and is not optimized for scale. Results might vary.")
        NebulaBase.__init__(self, mode="CLI", session_state=session_state)
        try:
            logging.warning(f"CACHE_PREFIX {self.CACHE_PREFIX}")
            self.redisObj = redis.StrictRedis(
                host=self.REDIS_IP, port=self.REDIS_PORT, password=self.REDIS_AUTH_TOKEN
            )
        except Exception as e:
            logging.critical(f"ERROR: {e}")
            # sys.exit()
            raise ErrorHandling

    def keyPartition(self, raw_key):
        """
        Split a cache key into its three ``_``-delimited components.

        Parameters
        ----------
        raw_key : str or bytes
            A raw ``{CACHE_PREFIX}_{timestamp}_{device_group}@{host}``
            key, as returned by `redis.StrictRedis.scan_iter`.

        Returns
        -------
        tuple of str
            ``(prefix, timestamp, device_group@host)``.
        """
        key = str(raw_key).replace("'", "")
        key_components = str(key).split("_")
        return key_components[0], key_components[1], key_components[2]

    def scanLatest(
        self,
    ):

        """
        Find the most recent report timestamp for every host currently cached.

        Scans every key under `CACHE_PREFIX`, keeping only the largest
        timestamp seen per host.

        Returns
        -------
        dict
            ``{device_group@host: latest_timestamp}``.
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
        Split a ``device_group@host`` id into its two parts.

        Parameters
        ----------
        host_id : str
            A ``device_group@host`` string, as produced by `keyPartition`.

        Returns
        -------
        host : str
        device_group : str
        """
        device_group = host_id.split("@")[0]
        host = host_id.split("@")[1]
        return host, device_group

    def getHosts(self, device_group_queried, host_queried):

        """
        Determine which hosts and/or device groups currently exist in the cache.

        Parameters
        ----------
        device_group_queried : str
            A device group name, or ``"all"``.
        host_queried : str
            A host name, or ``"all"``.

        Returns
        -------
        dict
            ``{"host_queried": ..., "device_group_queried": ..., "response": ...}``.
            The shape of `response` depends on which of
            `device_group_queried`/`host_queried` is ``"all"``:

            - both `"all"`: `response` is ``{host: [device_group, ...]}``
              for every cached host.
            - only `device_group_queried` is `"all"`: `response` is the
              list of device groups matching `host_queried` (or `[]` if
              `host_queried` isn't cached).
            - only `host_queried` is `"all"`: `response` is the list of
              device groups matching `device_group_queried` (or `[]`).
            - neither is `"all"`: `response` is a `bool` - whether that
              exact host/device-group pairing is cached.
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
        Fetch and unpickle the latest cached report for a device group/host pair.

        Parameters
        ----------
        device_group : str
        host : str

        Returns
        -------
        dict
            ``{"host_queried": host, "device_group_queried": device_group, "response": ...}``.
            `response` is the unpickled report dict on success, or `{}`
            if no cached entry exists for this pair or unpickling failed.
        key : str
            The ``device_group@host`` key looked up.
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
                logging.critical(f"ERROR: {e}")
                return {
                    "host_queried": host,
                    "device_group_queried": device_group,
                    "response": {},
                }, key
        else:
            logging.error(f"{key} not found in cache reports")
            return {
                "host_queried": host,
                "device_group_queried": device_group,
                "response": {},
            }, key

    def getIndividualVitals(self, device_group, host):
        """
        Format the cached memory/disk/CPU vitals for a device group/host pair as a summary string.

        Parameters
        ----------
        device_group : str
        host : str

        Returns
        -------
        dict
            ``{"error": False, "response": <summary str>}`` on success, or
            ``{"error": True, "response": <reason>}`` if nothing is
            cached for this pair or a field expected in the report is
            missing/malformed.

        Raises
        ------
        ErrorHandling
            If the cached report exists but is missing an expected
            vitals field.

        Notes
        -----
        Called by `getAssetsForAll`, which catches `ErrorHandling` and
        turns it into the same ``{"error": True, ...}`` shape rather
        than letting it propagate.
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
                logging.info(f"{key} at time: {time}\t mem: {mem}\t disk: {disk}\t cpu_cores: {cpu_core_use}\t cpu_percent {cpu_pct_use}")
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
                logging.critical(f"ERROR: {e}")
                # sys.exit()
                raise ErrorHandling
        else:
            logging.error(f"No key matches {key}")
            return {"error": True, "response": "no key matches {}".format(key)}

    def getIndividualContainers(self, device_group, host):
        """
        Format the cached container list for a device group/host pair as a summary string.

        Parameters
        ----------
        device_group : str
        host : str

        Returns
        -------
        dict
            ``{"error": False, "response": <summary str>}`` on success, or
            ``{"error": True, "response": <reason>}`` if nothing is
            cached for this pair or `apps_containers` is missing from
            the report.

        Raises
        ------
        ErrorHandling
            If the cached report exists but is missing an expected
            container field.

        Notes
        -----
        Called by `getAssetsForAll`, which catches `ErrorHandling` and
        turns it into the same ``{"error": True, ...}`` shape rather
        than letting it propagate.
        """

        response, key = self.unpickleData(device_group, host)
        data_dict = response["response"]
        if bool(data_dict):
            try:
                containers = str(data_dict["apps_containers"])
                time = str(data_dict["report_creation_time"])
                logging.info(f"{key} at time: {time} containers: {containers}")
                return {
                    "error": False,
                    "response": key
                    + " at time:"
                    + time
                    + " containers:"
                    + str(containers),
                }
            except Exception as e:
                logging.critical(f"ERROR: {e}")
                # sys.exit()
                raise ErrorHandling
        else:
            logging.error(f"No key matches {key}")
            return {"error": True, "response": "no key matches {}".format(key)}

    # not optimized at all

    def getAssetsForAll(self, asset, device_group_id="all", host_id="all"):
        """
        Fetch `"vitals"` or `"containers"` for every cached host matching a device group/host filter.

        Parameters
        ----------
        asset : str
            `"vitals"` or `"containers"`.
        device_group_id : str, optional
            A device group name, or `"all"` (default) to match any.
        host_id : str, optional
            A host name, or `"all"` (default) to match any.

        Returns
        -------
        dict
            ``{"error": bool, "response": ...}``. When both filters are
            `"all"` and nothing is cached, `response` is a "no data
            matches" string with `error=False` (not treated as a
            failure). Otherwise `response` is whatever
            `getIndividualVitals`/`getIndividualContainers` returned
            for each matching host, or an error string if that call
            raised.

        Notes
        -----
        CAUTION - doesn't scale: when either filter is `"all"`, this
        calls `scanLatest` and then `getIndividualVitals`/
        `getIndividualContainers` once per matching host, each of
        which re-scans and re-fetches from Redis. Not rewritten here,
        since fixing that is a real, separate change (batch the scan
        and pipeline the fetches), not a docs pass.
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
            logging.error(f"No data matches the query device_group:{device_group_id},host:{host_id}")
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
