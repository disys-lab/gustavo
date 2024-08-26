from gustavo.comms.Mapper import Mapper
import numpy as np
import time

mr = Mapper("example_mapper")


while True:

    localModel = 2*np.array([1,2,3,4,5,6])

    mr.Map(localModel,mr.key)
    buffer = np.array([0,0,0,0,0,0])
    allgather_dict,_,_ = mr.AllGather(buffer)

    f = open("/tmp/test.log", "a")
    print(allgather_dict,file=f)

    sum,_,_ = mr.Reduce(buffer,mr.SUM)

    print(sum,file=f)

    f.close()

    time.sleep(5)