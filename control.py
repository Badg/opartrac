''' Dynamic control architecture with copious Dilbert references.

The hope is to eventuall allow multiprocessing through this as well as 
multithreading, which is why several functions are currently one-line 
wrappers.
'''

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

        self.add_channel(self.name, prioritized=prioritized)

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
        # Initialize channel
        self.add_channel(name)
        # Create an event for the caller closing
        self.add_stop_flag(name)

    def add_channel(self, name, queue=None, prioritized=False):
        # Error traps
        if name == self.name and self.name in self.qs:
            raise AttributeError('"' + self.name + '" queue reserved for '
                'PHB.')

        # If a queue has been passed, check its type
        if queue:
            if type(queue) not in (PriorityQueue, Queue):
                AttributeError('Passed queue of incorrect type. Expected '
                    'Queue or PriorityQueue; received ' + str(type(queue)) +
                    '.')
            else:
                self.qs[name] = queue
        # Use a priority queue, or don't. Is this PHB competent?.
        elif prioritized:
            queue = PriorityQueue()
        else:
            queue = Queue()
        self.qs[name] = queue

    def get_channel(self, name):
        ''' Gets the queue associated with the name, or the PHB's own queue if
        the name is None.
        '''
        if not name:
            return self.qs[self.name]
        else:
            return self.qs[name]

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

    # def start_gui(self):
    #     self.guiThread = Thread(name="gui", target=sqGUId, args=())
    #     self.guiThread.daemon = False
    #     self.guiThread.start()
    #     self.add_q("gui", Queue())

    # def connect_gui(self):
    #     return self.qs["gui"]

    def run(self):
        gui_channel = self.get_channel("gui")
        while True:
            # Check for any stop flags
            for key, flag in self.stop_flags.items():
                if flag.is_set():
                    return
            success = request_task(gui_channel, self.name, 'print', 
                "Look at me, PHB, running 'round the Christmas tree!")
            time.sleep(1)

def spawn_PHB(name, caller=None, prioritized=False, target_thread=None, 
        *args, **kwargs):
    ''' Creates a pointy-haired boss in the thread specified by target, or if
    target is None, creates a new thread. Then returns the PHB.
    '''
    phb = PointyHairedBoss(name, caller=caller, prioritized=prioritized)
    if target_thread:
        # Error traps associated with targeting an existing thread object
        if target_thread.is_alive():
            raise AttributeError('Target thread cannot be running.')
        if target_thread._target:
            raise Warning('Overriding existing thread target: ' + 
                str(target_thread._target))
        target_thread._target = phb.run

    else:
        target_thread = Thread(name=name, target=phb.run, args=(), kwargs={})
        target_thread.daemon = False

    target_thread.start()
    phb.set_thread(target_thread)

    return phb

def poll_task(channel):
    ''' Does whatever is needed to poll commands from the queue, and, well, 
    whatever.
    '''
    if not channel.empty():
        try:
            command = channel.get(block=False)
        except Empty:
            return None
    else:
        return None

    if type(channel) is PriorityQueue:
        # Strip out the priority and just grab the dict
        command = command[1]

    return command


def done_task(channel):
    ''' Notifies a channel of task completion.
    '''
    channel.task_done()

def request_task(channel, origin, command, payload, priority=None, 
    *args, **kwargs):
    ''' Puts a request on the queue specified by channel.
    Priority is saturated at [0,1] and 0 represents lowest priority, 1
    represents highest. Don't blame me, blame sorted(). Returns true if 
    successful, false if unsuccessful (indicating queue is full).
    '''
    # Do some input pruning and error trappage
    if priority:
        _priority = min(priority, 1)
        _priority = max(_priority, 0)
    else:
        # Don't use 0 as a default because it could confuse people. 0 is the 
        # absolute lowest priority, so it's equivalent to 0.
        _priority = 0
    # Need this to fix sorted() behavior so that it makes more sense.
    _priority = 1 - _priority

    # Construct the item
    item = {'priority': priority, 'origin': origin, 'command': command, 
        'payload': payload}

    if type(channel) is PriorityQueue:
        item = (_priority, item)

    try:
        channel.put(item, block=False)
    except queue.Full:
        return False

    return True

def raise_stop_flag(flag):
    ''' Wrapper for setting a stop flag. '''
    flag.set()

def sqGUId():
    pass

if __name__ == '__main__':
    PHB = PointyHairedBoss()
    PHB.start_gui()
    PHB.run()