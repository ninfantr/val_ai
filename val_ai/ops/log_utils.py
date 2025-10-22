import os,sys, time
import logging
import textwrap

def log_redirect(filename):
    sys.stdout = open(filename, 'a')
    sys.stderr = open(filename, 'a')

def log_restore():
    sys.stdout = sys.__stdout__
    sys.stderr = sys.__stderr__

DEBUG_FILE = os.getenv("TTG_DEBUG_FILE",'debug_ttg.log')
if DEBUG_FILE:
    log_redirect(DEBUG_FILE)

# file_handler = logging.FileHandler(filename='debug_ttg.log')
# stdout_handler = logging.StreamHandler(stream=sys.stdout)
# handlers = [file_handler, stdout_handler]

logging.basicConfig(level=logging.DEBUG, stream = sys.stdout,
                    format='[%(levelname)-8s] %(module)s->%(funcName)s:%(lineno)d :: %(message)s',
                    # handlers= handlers
                    )
logger = logging.getLogger("ttg")

def txt_banner(text,width=100,display=True,symbol="-"):
    text = text.upper()
    lines = textwrap.wrap(text,break_long_words=False, width = width)
    content = "\n".join( line.center(width) for line in lines )
    txt = ""
    txt +=symbol.center(width,symbol) + "\n"
    txt +=content + "\n"
    txt +=symbol.center(width,symbol) + "\n"
    if display:  print(txt)
    else: return txt

class TaskProfiler():
    def __init__(self,name="TTG"):
        self.started_time = time.time()
        self.name = name
    
    def get_exec_time(self):
        return round(time.time() - self.started_time,2)
    
    # def get_memory_consumed(self):
    #     return 0
    
    def display_profile(self):
        print(f"[{self.name}]: Executed in {self.get_exec_time()} sec")
        #print(f"TASK {self.name}: Consumed in {self.get_memory_consumed()} MB")

