import multiprocessing
from multiprocessing import Queue
from stream_data import run_stream, Settings
from stream1 import run_stream_1 
from stream2 import run_stream_2 
from stream3 import run_stream_3 



if __name__ == '__main__':
    queue1 = Queue(maxsize=1)
    queue2 = Queue(maxsize=1)
    queue3 = Queue(maxsize=1)
    queue = []
  

    process1 = multiprocessing.Process(target=run_stream, args=([queue1,queue2,queue3],))
    process1.start()

    process2 = multiprocessing.Process(target=run_stream_1, args=(queue1,))
    process2.start()

    process3 = multiprocessing.Process(target=run_stream_2, args=(queue2,))
    process3.start()

    process4 = multiprocessing.Process(target=run_stream_3, args=(queue3,))
    process4.start()
 
 
    try:
        while True:
            pass
    except KeyboardInterrupt:

        process1.terminate()
        process2.terminate()
        process3.terminate()
        process4.terminate()
       
        process1.join()
        process2.join()
        process3.join()
        process4.join()