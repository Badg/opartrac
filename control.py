from queue import PriorityQueue, Queue, Empty
from threading import Thread
import threading

import time

class PointyHairedBoss():
    ''' Does this really need explaining? Well, yes, it probably does.

    + Should probably add some limited level of cross-communication ability.
    + Should also add dynamic ability for subordinates or superiors to add 
    just about anything to the run() method.
    + Should there be a definition for interfaces somewhere? That's, in a way,
    the aforementioned ability for subordinates/superiors to add code to run,
    but where should this be spec'ed out? Should the responsibility for the 
    interface definition be left entirely to everyone else?
    + Should self.elbonians be a list of names (strings), or also contain
    references to the objects that each of the elbonians have? The latter 
    would allow for more than just elbonian objects to be added to the 
    + Need to define a new type of attribute error for "elbonian does not 
    exist"

    '''
    _channel = "_control"

    def __init__(self, name, caller=None, prioritized=False):
        self.name = name
        self.thread = None
        self.elbonians = []
        self.qs = {}
        self.stop_flags = {}
        if caller:
            # if not q_caller:
            #     raise AttributeError('If PHB has a given caller, caller must '
            #         'be given a queue.')
            # else:
            #     add_elbonian(caller, queue=q_caller)
            self.add_elbonian(caller)

        self.add_queue(_channel, prioritized=prioritized)

    def set_thread(self, thread):
        self.thread = thread

    def add_elbonian(self, name, queue=None):
        ''' Boilerplate operations for interfacing with any lower-level 
        system. AKA, we're outsourcing to Elbonia.

        If no queue is passed, it will return a queue. Generally, queues 
        should only be passed from the main thread, implying the PHB is 
        running in a secondary thread. Also returns an Event ("stop flag") to 
        raise if or when the subordinate completes.

        If a queue is passed (implying the phb is being spawned from another 
        thread / process) it will return only the stop flag. 

        '''
        # First record the fact that we've got an elbonian.
        self.elbonians.append(name)
        # Initialize communications list
        self.add_comms(name)
        # Create an event for the caller closing
        self.add_stop_flag(name)
        # Add the queue
        self.add_queue(name)

    def get_channel(self):
        return self.get_queue(_channel)

    def add_stop_flag(self, name, flag=None):
        '''Safely creates a stop flag for the <name>d elbonian.'''
        # Error traps
        if name not in self.elbonians:
            raise AttributeError('Subordinate "' + name + '" does not exist.')

        if not flag:
            flag = threading.Event()

        self.stop_flags[name] = flag

    def get_stop_flag(self, name):
        ''' Gets the stop flag for the <name>d elbonian.'''
        return self.stop_flags[name]

    def add_queue(self, name, queue=None, prioritized=False):
        # Error traps
        if name = _channel and _channel in self.qs:
            raise AttributeError('"' + _channel + '" queue reserved for PHB.')

        # If a queue has been passed, check its type
        if queue:
            if type(queue) not in (PriorityQueue, Queue):
                AttributeError('Passed queue of incorrect type. Expected '
                    'Queue or PriorityQueue; received ' + str(type(queue)) +
                    '.')
            else:
                pass
        # Use a priority queue, or don't. Is this PHB competent?.
        elif prioritized:
            queue = PriorityQueue()
        else:
            queue = Queue()
        self.qs[name] = queue

    def get_queue(self, name):
        ''' This method actually probably doesn't have much use, because 
        '''
        return self.qs[name]

    def refresh_queue(self, name):
        thisqueue = self.get_queue(name)

    def put_on_queue(self, name, obj):
        self.qs[name].put(obj)

    def check_queue(self, name):

    # def start_gui(self):
    #     self.guiThread = Thread(name="gui", target=sqGUId, args=())
    #     self.guiThread.daemon = False
    #     self.guiThread.start()
    #     self.add_q("gui", Queue())

    # def connect_gui(self):
    #     return self.qs["gui"]

    def run(self):
        while True:
            if self.stop_flags["gui"].is_set():
                return
            self.put_on_queue("gui", "Look at me, PHB, running 'round the "
                "Christmas tree!")
            time.sleep(1)

def spawn_PHB(name, caller=None, prioritized=False, target_thread=None, 
        *args, **kwargs):
    ''' Creates a pointy-haired boss in the thread specified by target, or if
    target is None, creates a new thread.
    '''
    phb = PointyHairedBoss(name, caller=caller, prioritized=prioritized)
    if not target_thread:
        target_thread = Thread(name=name, target=phb.run, args=(), kwargs={})
        target_thread.daemon = False
        target_thread.start()
    phb.set_thread(target_thread)

    return phb

def poll(channel):
    ''' Does whatever is needed to poll commands from the queue, and, well, 
    whatever. Priority queues are yet to be implemented; currently the 
    priority is stripped and the task simply returned.
    '''
    try:
        while not self.qs[name].empty():
            command = channel.get(block=False)
        except Empty:
            pass
    if type(thisqueue) is PriorityQueue:
        priority = command.pop[0]
    else:
        priority = None

    # Change this to dict comp
    origin, command, payload, *etc = command

    return {'priority': priority, 'origin': origin, 'command': command, 
        'payload': payload}


def release(channel):
    ''' Notifies a channel of task completion.
    '''
    channel.task_done()

def request(channel, origin, command, payload, priority=None, *args, **kwargs):
    ''' Puts a request on the queue specified by channel.
    '''
    pass

def raise_stop_flag(flag):
    ''' Wrapper for setting a stop flag. '''
    flag.set()

def sqGUId():
    pass

if __name__ == '__main__':
    PHB = PointyHairedBoss()
    PHB.start_gui()
    PHB.run()