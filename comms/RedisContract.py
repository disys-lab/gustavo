import logging, redis,time,os

class RedisContract:
    """
    Base class for all types of Contracts. Contains all Contract attributes

    Attributes
    ----------
    key_list : list
        list of keys

    Methods
    -------

    * `load()`
        Loads redis details from os.environ.

    * `registerNewKey(key)`
        registers new key on contract

    * `loadRedis()`
        Connect to redis given redisDBHost,redisDBPort and redisDBPwd

    * `setChunk(key, chunk, chunk_content, address)`
        Set the chunk for a particular key

    * `checkChunkExists(key, chunk)`
        Check if the chunk exists for a particular key

    * `getChunk(key, chunk)`
        Get chunk for a particular key

    * `getChunkUpdater(key, chunk)`
        Get the updater (address) of chunk for a particular key

    * `getLastUpdateTime(key, chunk)`
        Get the last updated time of chunk for a particular key

    * `getMapperLength()`
        gets mapper length, i.e. number of unique keys on the mapper. applicable only in case of Mapper scarlets.

    * `getKey()`
        if given an index key_index, retrieves the key at that location. applicable in case of Mapper scarlets.

    """

    def __init__(self,contractName):

        self.contractName = contractName

        self.key_list = []

        self.load()

    def load(self):

        """
        Loads redis details from os.environ.
        """

        if "REDIS_DB_HOST" not in os.environ.keys():
            raise Exception("REDIS_DB_HOST not set in os.environ")

        if "REDIS_DB_PORT" not in os.environ.keys():
            raise Exception("REDIS_DB_PORT not set in os.environ")

        if "REDIS_DB_PWD" not in os.environ.keys():
            raise Exception("REDIS_DB_PWD not set in os.environ")

        self.redisDBHost = os.environ["REDIS_DB_HOST"]
        self.redisDBPort = os.environ["REDIS_DB_PORT"]
        self.redisDBPwd = os.environ["REDIS_DB_PWD"]

    def registerNewKey(self, key):

        """
        registers new key on contract

        Parameters
        ----------
        key : string
            the key to be registered

        Returns
        -------

        ret_val : boolean
            represents whether the register method was successful on the SmartContract

        """

        key = str(key)
        r, status, exception = self.loadRedis()
        if status:
            if not r.exists(self.contractName + "_key-value"+":"+key):
                r.set(self.contractName + "_key-value"+":"+key,"exists")
                return True
            else:
                return True

        return False


    def loadRedis(self):
        """
        Connect to redis given redisDBHost,redisDBPort and redisDBPwd

        Returns
        -------

        r : redis object
            the object that can connect to redis

        success : boolean
            flag that indicates whether the connect succeeded

        exception : Exception
            the exception that is thrown in case of an error

        """
        try:

            logging.info(self.redisDBHost,self.redisDBPort,self.redisDBPwd)

            r = redis.StrictRedis(host=self.redisDBHost, port=int(self.redisDBPort),
                                  password=self.redisDBPwd)
            r.ping()
            return r,True,None

        except Exception as exception:
            logging.error("could not connect to redis due to exception {}".format(exception))
            return None,False,exception


    def setChunk(self, key, chunk, chunk_content, address):
        """
        Set the chunk for a particular key

        Parameters
        ----------

        key : string
           the key id

        chunk : int
            the chunk id to be set

        chunk_content : string
            binary string that represents the chunk content

        address : string
            the address of the agent setting the string


        Returns
        -------

        ret_val : boolean
            flag that represents whether the set operation was successful or not

        exception : Exception
            Exception thrown in case of an error, None in case of no exception
        """


        r, status, exception = self.loadRedis()
        if status:
            r.hmset(self.contractName+"_key-value"+":"+str(key)+":"+str(chunk),{
                                                                                    "updater":address,
                                                                                    "content":chunk_content,
                                                                                    "lastUpdatedTime":time.time()
                                                                                })
            return True,None
        else:
            return status,exception


    def checkChunkExists(self, key, chunk):
        """
        Check if the chunk exists for a particular key

        Parameters
        ----------

        key : string
           the key id

        chunk : int
            the chunk id to be set

        Returns
        -------

        ret_val : boolean
            flag representing the existence of the flag
        """


        r, status, exception = self.loadRedis()
        if status:
            if r.exists(self.contractName+"_key-value"+":"+str(key)+":"+str(chunk)):
                return True
        return False


    def getChunk(self,key, chunk):
        """
        Get chunk for a particular key

        Parameters
        ----------

        key : string
           the key id

        chunk : int
            the chunk id to be set

        Returns
        -------

        chunk_content : string
            binary string representing the chunk content, defaults to empty string in case of failure

        """

        r, status, exception = self.loadRedis()

        if status:
            if r.exists(self.contractName+"_key-value"+":"+str(key)+":"+str(chunk)):
                chunkDict = r.hgetall(self.contractName+"_key-value"+":"+str(key)+":"+str(chunk))
                return chunkDict[b'content']
        return b''


    def getChunkUpdater(self,key, chunk):
        """
        Get the updater (address) of chunk for a particular key

        Parameters
        ----------

        key : string
           the key id

        chunk : int
            the chunk id to be set

        Returns
        -------

        chunk_updater : string
            address of the last updater, None in case of failure

        """

        r, status, exception = self.loadRedis()
        if status:
            if r.exists(self.contractName + "_key-value" + ":" + str(key) + ":" + str(chunk)):
                chunkDict = r.hgetall(self.contractName + "_key-value" + ":" + str(key) + ":" + str(chunk))
                return chunkDict[b'updater']
        return None


    def getLastUpdateTime(self, key, chunk):
        """
        Get the last updated time of chunk for a particular key

        Parameters
        ----------

        key : string
           the key id

        chunk : int
            the chunk id to be set

        Returns
        -------

        lastUpdatedTime : string
            time of the last update, empty string in case of failure

        """
        r, status, exception = self.loadRedis()
        if status:
            if r.exists(self.contractName + "_key-value" + ":" + str(key) + ":" + str(chunk)):
                chunkDict = r.hgetall(self.contractName + "_key-value" + ":" + str(key) + ":" + str(chunk))
                return chunkDict[b'lastUpdatedTime'], None
        return ""


    def getKeysLength(self):

        """
        gets mapper length, i.e. number of unique keys on the mapper. applicable only in case of Mapper scarlets.
        """

        r, status, exception = self.loadRedis()

        if status:

            comprehensive_keys_list = r.keys(self.contractName + "_key-value:*")

            self.key_list = [key.decode("utf-8").split(":")[1] for key in comprehensive_keys_list]
            if not len(self.key_list):
                logging.warning("getMapperLength yielded 0 keys for mapper:{}".format(self.contractName))
            return len(self.key_list)

        else:
            return 0

    def getKey(self,key_index):
        """
        if given an index key_index, retrieves the key at that location. applicable in case of Mapper scarlets.
        """
        return self.key_list[key_index]
