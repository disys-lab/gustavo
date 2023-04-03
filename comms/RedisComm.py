import logging, pickle, zlib, yaml, os
from gustavo.comms.RedisContract import RedisContract


class RedisComm:
    """
    Redis class used to communicate local insights to Redis running on manager node

    Attributes
    ----------

    scarletName : string
        name of communication primitive

    address : string
        a unique address for identifying this node

    identity_config : dict
        dictionary current node's identity read through the identity file.

    contract : Contract
        the contract object that handles communication with the SmartContracts

    Methods
    -------

    * `_verifyScarletParameters()`
        Verifies whether scarlet parameters match

    * `loadContract()`
        Loads contract details from remote DB

    * `Pull(modelLocal, key="0x0", calcWD=False, average=False)`
        Pull the global model from chain and update the local model

    * `Push( modelLocal, key="0x0", wait4Tx=None)`
        Push the local model to the chain.

    """

    def __init__(self, scarletName):

        self.scarletName = scarletName
        self.contract = None
        self.address = ""

        self.identity_config = self.readIdentityFile()
        self.address = self.identity_config["address"]

    def readIdentityFile(self):

        id_file = "/tmp/identity.yaml"
        if "ID_FILE" in os.environ.keys():
            id_file = os.environ["ID_FILE"]

        stream = open(id_file, "r")
        try:
            identity_config = yaml.safe_load(stream)
            return identity_config

        except yaml.YAMLError as exception:
            click.echo(
                click.style(
                    "failure opening identity file : {} with exception: {}".format(
                        config_file, exception
                    ),
                    fg="red",
                )
            )
            return



    def loadContract(self):

        # initialize contract
        self.contract = RedisContract(
            self.scarletName
        )

    def Pull(
        self,
        modelLocal,
        key="0x0"
    ):

        """
        Pull the global model from chain and update the local model.

        Parameters
        ----------
        modelLocal : numpy array
            A unidimensional numpy array representing the local estimate
        key: string
            Used as key for Mapper
        calcWD : bool
            Boolean indicating whether to calculate weight difference with the global model
        average : bool
            Boolean indicating whether to average the global model with the local model or not

        Returns
        -------
        modelOut:
            The updated model
        numUpdatedChunks:
            The number of chunks which were successfully pulled from global model

        """

        val = self.contract.checkChunkExists(key, 0)
        if val:

            modelBytes = self.contract.getChunk(key, 0)

            modelBytes = zlib.decompress(modelBytes)
            modelOut = pickle.loads(modelBytes)

            return modelOut, True
        else:
            logging.error("chunk key: {} not found".format(key))
            return modelLocal, False

    def Push(self, modelLocal, key="0x0"):
        """
        Push the local model to the chain.

        Parameters
        ----------
        modelLocal : numpy array
            A unidimensional numpy array representing the local estimate
        key: string
            Used as key for Mapper
        wait4Tx (optional): list
            contains the wait4Tx bool as well as wait4TxRecieptTime
            If empty, the config default is taken


        Returns
        -------
        successChunksList:
            List with one element, either 0/1 depending on whether the push was successful or not
        """

        # check if any debug values have been sent in wait4Tx

        modelBinCompr = pickle.dumps(modelLocal, protocol=pickle.HIGHEST_PROTOCOL)
        modelBinCompr = zlib.compress(modelBinCompr, level=9)

        status, exception = self.contract.setChunk(
            key, 0, modelBinCompr, self.address
        )

        if not status:
            logging.error("fail to set chunk for key: {}".format(key))

        return [status]
