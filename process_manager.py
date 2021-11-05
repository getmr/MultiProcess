import signal
import os
import logging
import multiprocessing
import time
from .importer import import_from_string

 
HANDLED_SIGNALS = (
    signal.SIGINT,  # Unix signal 2. Sent by Ctrl+C.
    signal.SIGTERM,  # Unix signal 15. Sent by `kill <pid>`.
)
logger = logging.getLogger()


class Multiprocess(object):
    def __init__(self, workers, server):
        self.workers = workers
        self.server = server
        self.pid = os.getpid()
        self.should_exit = False
        self.processes = []
    
    def signal_handler(self, sig, frame):
        self.should_exit = True
    
    def run(self):
        self.startup()
        self.shutdown()
    
    def startup(self):
        message = "Started parent process [{}]".format(str(self.pid))
        print(message)
        for sig in HANDLED_SIGNALS:
            signal.signal(sig, self.signal_handler)
        for _ in range(self.workers):
            process = multiprocessing.Process(target=self.server)
            process.start()
            self.processes.append(process)
        
        while True:
            process_status_list = [process.is_alive() for process in self.processes]
            if not any(process_status_list) or self.should_exit:
                break
            else:
                time.sleep(0.1)

    def shutdown(self):
        for process in self.processes:
            if process.is_alive():
                print(f"stoping child process {process}")
                process.terminate()
        message = "Stopping parent process [{}]".format(str(self.pid))
        print(message)


class Server(object):
    def __init__(self, app):
        self.app = app
    
    def run(self):
        self.serve(self.app)
    
    def serve(self, app):
        app = import_from_string(app)
        for sig in HANDLED_SIGNALS:
            signal.signal(sig, self.signal_handler)
        message = "Started server process [%d]"
        logger.info(message % os.getpid())
        app()
    
    def signal_handler(self, sig, frame):
        message = "Finished server process [%d]"
        logger.info(message % os.getpid())
        os.kill(os.getpid(), signal.SIGKILL)