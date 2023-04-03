from gustavo.comms.RedisComm import RedisComm

import logging

import operator
import numpy as np






class Mapper(RedisComm):
    """
    Mapper Scarlet maps keys to values. Values could be anything such as model parameters, arrays etc.
    This Mapper inherits from multiple classes. However, at run time depending on the mode of the scarlet declaration,
    the classes are initialized.

    Attributes
    ----------

    key : str
        A unique string used to identify edge device

    Methods
    -------

    * `refresh()`
        refresh contract details

    * `_registerNewKey(key)`
        registers new key by calling the corresponding underlying contract function

    * `Map(modelLocal,key)`
        maps model parameters to a given key

    * `AllGather(modelLocal)`
        Performs an AllGather operation in which all the key-value pairs are obtained.

    * `Reduce(modelLocal,op)`
        Performs a Reduce operation which comprises of an AllGather followed by an operation on all the values
        obtained thus far.

    * `resetAll(modelLocal)`
        Resets all the key-value pairs
    """

    def __init__(self, scarletName):

        RedisComm.__init__(self,scarletName)
        self.key = str(self.address)

        self.refresh()

        self.SUM = operator.add
        self.MUL = operator.mul
        self.MAX = np.maximum
        self.MIN = np.minimum
        self.opArray = [self.SUM, self.MUL, self.MAX, self.MIN]

    def performOperation(self, modelLocal, globalModel, operation):
        """
        performs the given operation
        Parameters
        ----------
        modelLocal : numpy array
            Argument 1 of the operation
        globalModel : numpy array
            Argument 2 of the operation
        Returns
        ----------
        retval : return value is None if the operation is not supported, else it returns the result
        """
        if operation not in self.opArray:
            return None
        else:
            return operation(modelLocal, globalModel)


    def refresh(self):
        """refresh contract details"""
        self.loadContract()

        self.key = str(self.address)

        if not self._registerNewKey(self.key):
            logging.critical("Key: {} already being used".format(self.key))

    def _registerNewKey(self, key):
        """registers new key by calling the corresponding underlying contract function

        Attributes
        ----------
        key : string
            value of key to be registered

        """
        keyRegisterSuccess = self.contract.registerNewKey(key)
        return keyRegisterSuccess

    def Map(self, modelLocal, key):

        """maps model parameters to a given key

        Attributes
        ----------
        modelLocal : numpy array
            the content concerning modelLocal

        key : string
            value of key to be registered

        Returns
        -------

        successChunksList : list
            concerns the chunks which were successfully mapped

        status : boolean
            status of the Map operation

        exception : Exception
            exception if any else it will be None

        """

        successChunksList = []
        try:

            self.refresh()
            successChunksList = self.Push(modelLocal, key)
        except Exception as exception:
            logging.error("{}.Map failed", self.scarletName)
            return successChunksList, False, exception
        return successChunksList, True, None

    def AllGather(self, modelLocal):
        """Performs an AllGather operation in which all the key-value pairs are obtained from the decentralized
        infrastructure.

        Attributes
        ----------
        modelLocal : numpy array
            the content concerning modelLocal

        Returns
        -------

        allgather_dict : dict
            the dictionary containing all key value pairs

        status : boolean
            status of the Map operation

        exception : Exception
            exception if any else it will be None

        """
        allgather_dict = {}
        try:

            self.refresh()

            mapperLength = self.contract.getKeysLength()
            for key_index in range(int(mapperLength)):
                key = self.contract.getKey(key_index)
                modelOut, status = self.Pull(modelLocal, key)
                if not status:
                    logging.error(
                        "{}.AllGather.Pull failed wfor key :{}".format(
                            self.scarletName, key
                        )
                    )
                allgather_dict[key] = modelOut

            return allgather_dict, True, None

        except Exception as exception:
            logging.error(
                "{}.AllGather failed with exception {}".format(
                    self.scarletName, exception
                )
            )
            return allgather_dict, False, exception

    def Reduce(self, modelLocal, op):
        """Performs a Reduce operation which comprises of an AllGather followed by an operation on all the values
        obtained thus far. The choice of operations is SUM,MAX,MIN,MULT. In case of MAX,MIN and MULT it will be an
        element wise operation.

        Attributes
        ----------
        modelLocal : numpy array
            the content concerning modelLocal

        op : operation
            any one of the 4 operations SUM,MAX,MIN,MULT

        Returns
        -------

        sumV : numpy array
            final value after carrying out the operation sequentially on all values.

        status : boolean
            status of the Map operation

        exception : Exception
            exception if any else it will be None

        """
        sumV = modelLocal
        allgather_dict, status, exception = self.AllGather(modelLocal)
        if status:
            for key in allgather_dict.keys():
                sumV = self.performOperation(allgather_dict[key], sumV, op)
            return sumV, status, None
        else:
            return sumV, status, exception

    def resetAll(self, modelLocal):
        """Resets all the key-value pairs

        Attributes
        ----------
        modelLocal : numpy array
            the content concerning modelLocal

        Returns
        -------

        successChunksList : list
            concerns the chunks which were successfully reset

        exception : Exception
            exception if any else it will be None

        """
        successChunksList = []
        try:
            self.refresh()
            mapperLength = self.contract.getKeysLength()
            for key_index in range(int(mapperLength)):
                key = self.contract.getKey(key_index)
                successChunksList = self.Push(modelLocal, key)
        except Exception as exception:
            logging.error("{}.resetAll failed", self.scarletName)
            return successChunksList, exception
        return successChunksList, None
