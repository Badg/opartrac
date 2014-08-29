''' Dynamic control architecture with copious Dilbert references.

The hope is to eventually allow multiprocessing through this as well as 
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
    + Should replace discrete minions vs CEO lists as priority adjustments.

    '''

    def __init__(self, name, tasks, caller=None, prioritized=False, 
        slave=False, *args, **kwargs):
        # What about targeting an existing thread?
        # Trappage and stuff
        if type(tasks) is not dict:
            raise AttributeError('Tasks must be a dictionary.')

        # if target_thread:
        #     # Error traps associated with targeting an existing thread object
        #     if target_thread.is_alive():
        #         # Ah, but what about running in the current thread? The 
        #         # problem isn't so much that the thread is running, but 
        #         # rather, are we capable of running in it?
        #         raise AttributeError('Target thread cannot be running.')
        #     if target_thread._target:
        #         raise Warning('Overriding existing thread target: ' + 
        #             str(target_thread._target))
        #     target_thread._target = phb.run

        # else: (if not slave:)
        # This may need to be an RLock for internal (recursive) calls to ex:
        # add_channel from add_elbonian would block.
        self.lock = threading.Lock()

        # Input processing
        if 'stop' not in tasks:
            tasks['stop'] = (lambda *args, **kwargs: None)
        self.name = name
        self.tasks = tasks
        self.CEO = None
        self.elbonians = []
        self.coworkers = {}
        self.qs = {}
        self.stop_flags = {}
        self.tasks = tasks
        self.minions = []
        if caller:
            if type(caller) is str:
                self.add_elbonian(caller)
            elif type(caller) is PointyHairedBoss:
                self.CEO = caller.name
                self.add_coworker(caller)
            else: 
                raise AttributeError('Caller must be a PHB or string.')

        self.add_channel(self.name, prioritized=prioritized)
        self.add_stop_flag(self.name)
        # Now let's boot up the thread and start the engine
        if not slave:
            target_thread = Thread(name=name, target=self.run, args=(), 
                kwargs={})
            target_thread.daemon = False
            target_thread.start()
            # Need error traps
            self.thread = target_thread
        else:
            self.thread = None

    def run(self):
        while True:
            self.run_once()
        
            # Check for a stop
            stop, result = self.check_stop()
            # If there's been any non-false return of 
            if stop:
                return result

    def run_once(self):
        # Note that there's no real need to check for stop flags because this
        # will only execute once, and we're not concerned with immediate 
        # shutdown (or are we?)
        success = request_task(self.get_channel("gui"), self.name, 'print', 
            "Look at me, PHB, running 'round the Christmas tree!")
        time.sleep(1)

    def process_tasks(self):
        ''' Calls up the process_tasks function.
        '''
        pass

    def add_coworker(self, phb):
        # acquire a lock
        with self.lock:
            # Error traps
            if phb.name in self.coworkers:
                raise AttributeError('Coworkers must have unique names. "' + 
                    phb.name + '" already in coworkers.')

            # The phb appears to be valid, so let's add it and link it up
            self.coworkers[phb.name] = phb
        self.add_channel(phb.name, phb.get_channel())
        self.add_stop_flag(phb.name, phb.get_stop_flag())

    def add_minion(self, name, prioritized=False):
        ''' Creates a subordinate PHB, linking the two. Stopping the superior
        will automatically raise subordinate stop flags.
        '''
        with self.lock:
            # Trappage
            if name in self.coworkers:
                raise AttributeError('Minions must have unique names. ' + 
                    name + ' already among coworkers.')

        # Create a subordinate PHB and add it to the list of minions
        self.coworkers[name] = PointyHairedBoss(name, caller=self, 
            prioritized=prioritized)

        # Reacquire lock
        with self.lock:
            self.minions.append(name)

    def add_elbonian(self, name):
        ''' Boilerplate operations for interfacing with any external, non-PHB
        system. AKA, we're outsourcing to Elbonia.

        If no queue is passed, it will return a queue. Generally, queues 
        should only be passed from the main thread, implying the PHB is 
        running in a secondary thread. Also returns an Event ("stop flag") to 
        raise if or when the subordinate completes.

        If a queue is passed (implying the phb is being spawned from another 
        thread / process) it will return only the stop flag. 

        '''
        with self.lock:
            # First record the fact that we've got an elbonian.
            self.elbonians.append(name)
        # Initialize channel
        self.add_channel(name)
        # Create an event for the caller closing
        self.add_stop_flag(name)

    def add_task(self, name, callable_task):
        with self.lock:
            # Trappage
            if name in self.tasks:
                raise AttributeError('Task "' + name + '" already exists.')

            # Add the task
            self.tasks[name] = callable_task

    def replace_task(self, name, callable_task):
        with self.lock:
            # Trappage
            if name not in self.tasks:
                raise AttributeError('Task "' + name + '" does not exist.')

            self.tasks[name] = callable_task

    def run_task(self, name, *args, **kwargs):
        self.tasks[name](args, kwargs)

    def add_channel(self, name, queue=None, prioritized=False):
        with self.lock:
            # Error traps
            if name == self.name and self.name in self.qs:
                raise AttributeError('"' + self.name + '" queue reserved for '
                    'PHB.')
            if name in self.qs:
                raise AttributeError('Channel "' + name + '" already exists.')

            # If a queue has been passed, check its type
            if queue:
                if type(queue) not in (PriorityQueue, Queue):
                    AttributeError('Passed queue of incorrect type. Expected '
                        'Queue or PriorityQueue; received ' + 
                        str(type(queue)) + '.')
                else:
                    self.qs[name] = queue
            # Use a priority queue, or don't. Is this PHB competent?.
            elif prioritized:
                queue = PriorityQueue()
            else:
                queue = Queue()
            self.qs[name] = queue

    def get_channel(self, name=None):
        ''' Gets the queue associated with the name, or the PHB's own queue if
        the name is None.
        '''
        with self.lock:
            if not name:
                return self.qs[self.name]
            else:
                return self.qs[name]

    def add_stop_flag(self, name, flag=None):
        '''Safely creates a stop flag for the <name>d elbonian.'''
        # Error traps
        #if name not in self.elbonians:
            #raise AttributeError('Subordinate "' + name + '" does not exist.')
        with self.lock:
            if name in self.stop_flags:
                raise AttributeError('Flag "' + name + '" already exists.')

            if not flag:
                flag = threading.Event()

            self.stop_flags[name] = flag

    def replace_stop_flag(self, name, flag):
        with self.lock:
        # Trappage
            if name not in self.stop_flags:
                raise AttributeError('Stop flag "' + name + 
                    '" does not exist.')
            # At some point this will need to be expanded to other kinds 
            # of events as well.
            if type(flag) is not threading.Event:
                raise AttributeError('Flag must be a threading event.')

            self.stop_flags[name] = flag

    def get_stop_flag(self, name=None):
        ''' Gets the stop flag for the <name>d elbonian. If no name, returns
        own stop flag.'''
        with self.lock:
            if not name:
                return self.stop_flags[self.name]
            else:
                return self.stop_flags[name]

    def check_stop(self):
        # Check for any stop flags.
        # The flags themselves are threadsafe. Should I add some thread 
        # protection for stoptask?
        for key, flag in self.stop_flags.items():
            if flag.is_set():
                # Call the stop task, passing the originator of the stop call
                # as an argument. Note that run_task returning anything that
                # will be interpreted as False will result in the stop flag
                # being ignored.
                stoptask = self.run_task('stop', caller=key, flag=flag)

                # Support ignoring the stop flag
                if stoptask == "_ignore_stop_flag":
                    continue
                else:
                    return True, stoptask
        return False, None

def duplicate_PHB(name, caller=None, target_thread=None, *args, **kwargs):
    pass
    # Need to add this at some point.

def process_tasks(requests, tasks):
    ''' Provides a common mechanism to execute requested tasks in a relatively
    dumb (but predictable) way.
    '''
    pass

def poll_requests(channel):
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

if __name__ == '__main__':
    PHB = PointyHairedBoss()
    PHB.run()