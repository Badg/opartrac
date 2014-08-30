''' Dynamic control architecture with copious Dilbert references.

The hope is to eventually allow multiprocessing through this as well as 
multithreading, which is why several functions are currently one-line 
wrappers.
'''

from queue import PriorityQueue, Queue, Empty
from threading import Thread
import threading
import collections

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

    def __init__(self, name, tasks={}, caller=None, prioritized=False, 
        slave=False, *args, **kwargs):
        # What about targeting an existing thread?
        # Trappage and stuff

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

        self.name = name
        # Input processing (need to rename the "private" members)
        try:
            self.tasks = tasks
            if 'stop' not in self.tasks:
                self.tasks['stop'] = (lambda *args, **kwargs: None)
        except (TypeError, AttributeError):
            raise TypeError('Tasks must be a dictionary or empty.')
        # self.CEO = None
        self.elbonians = []
        self._coworkers = {}
        self.qs = {}
        self.stop_flags = {}
        self.tasks = tasks
        # _torepeat schedules a task for every iteration
        self._torepeat = []
        self._tore_lock = threading.RLock()
        self._todo = collections.deque([])
        # Yes, deques are threadsafe, but we're doing bulk operations in 
        # run_once and don't want extra shit added to the todo list while 
        # it's being burned down (note that this shouldn't happen though, 
        # as only the active thread should be capable of adding items to the 
        # todo list.)
        self._todo_lock = threading.RLock()
        # self.minions = []
        if caller:
            if type(caller) is str:
                self.add_elbonian(caller)
            elif type(caller) is PointyHairedBoss:
                self.CEO = caller.name
                self.link_phb(caller)
            else: 
                raise AttributeError('Caller must be a PHB or string.')

        self.add_channel(self.name, prioritized=prioritized)
        self.add_stop_flag(self.name)

        self._my_queue = self.qs[self.name]
        self._my_stop = self.stop_flags[self.name]

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

        # try:
        #     super(PointyHairedBoss, self).__init__(**kwargs)
        # except TypeError:
        #     # No super / based off object, so move along then
        #     pass

    def run(self):
        while True:
            # Check for a stop
            stop, result = self._check_stop()
            # If there's been any non-false return of 
            if stop:
                return result

            # # Schedule any recurring events
            # for key, task in self._torepeat.items():
            #     with self._todo_lock:
            #         self._todo.append(task)

            self.run_once()

    def run_once(self, limit=None, clear=False, *args, **kwargs):
        ''' Refreshes tasks, turning received requests into todos, and then
        burns the entire todo list.
        Limit -> maximum time to take
        Clear -> only used if there's a limit, specifies whether to keep or 
        discard the todo

        Limit and clear are yet to be implemented
        '''
        # Note that there's no real need to check for stop flags because this
        # will only execute once, and we're not concerned with immediate 
        # shutdown (or are we?)
        self._get_requests()
        with self._tore_lock, self._todo_lock:
            self._todo.extend(self._torepeat)
            self._order_todo()
            self._burn_todo()

        # success = request_task(self.get_channel("gui"), self.name, 'print', 
        #     "Look at me, PHB, running 'round the Christmas tree!")

    def _burn_todo(self, *args, **kwargs):
        ''' Burns the entire todo list.
        '''
        with self._todo_lock:
            while len(self._todo) > 0:
                task = self._todo.popleft()
                t_args, t_kwargs = task['payload']
                to_call = task['command']
                repeated = task['repeat']
                # origin = task['origin']
                # priority = task['priority']
                self.tasks[to_call](*t_args, **t_kwargs)
                # Cannot naively call complete_request, since recurring tasks
                # will cause it to be called inappropriately.
                if repeated == None:
                    self._complete_request()

    def process_tasks(self):
        ''' Calls up the process_tasks function.
        '''
        pass

    def link_phb(self, phb):
        # I'd love to have this include some kind of prioritization preference
        # Acquire a lock
        with self.lock:
            # Error traps
            if phb.name in self._coworkers:
                raise AttributeError('Coworkers must have unique names. "' + 
                    phb.name + '" already in coworkers.')

            # The phb appears to be valid, so let's add it and link it up
            self._coworkers[phb.name] = phb
        self.add_channel(phb.name, phb.get_channel())
        self.add_stop_flag(phb.name, phb.get_stop_flag())

        # Two-way street, yo
        if self not in phb.list_coworkers():
            phb.link_phb(self)

    def add_minion(self, name, prioritized=False):
        ''' Creates a subordinate PHB, linking the two. Stopping the superior
        will automatically raise subordinate stop flags.
        '''
        with self.lock:
            # Trappage
            if name in self._coworkers:
                raise AttributeError('Minions must have unique names. ' + 
                    name + ' already among coworkers.')

        # Create a subordinate PHB and add it to the list of minions
        self._coworkers[name] = PointyHairedBoss(name, caller=self, 
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

    def list_coworkers(self):
        if len(self._coworkers) > 1:
            keys, coworkers = self._coworkers.items()
            return coworkers
        elif len(self._coworkers) == 1:
            return self._coworkers.values()
        else:
            return []

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
        ''' This may be a few inches from deprecation.

        '''
        self.tasks[name](args, kwargs)

    def make_request(self, target, command, payload, return_channel=None, 
        priority=None):
        # Convenience wrapper for request_task
        request_task(target, self, command, payload, return_channel, priority)

    def _get_requests(self):
        # Be cognisant of the fact that other threads can inject items into
        # the queue while we're in the process of emptying it. May want to 
        # add a lock.
        _temp_todo = []
        _temp_tore = []
        temp_request = True
        while temp_request:
            # Grab the request
            temp_request = process_request(self._my_queue)
            # Make sure there was, in fact, a request (race condition)
            if temp_request:
                # Allocate to either single requests or repeating requests
                if temp_request['repeat'] == True:
                    _temp_tore.append(temp_request)
                    # Slightly premature "mission accomplished" -- may move
                    self._complete_request()
                elif temp_request['repeat'] == False:
                    pass
                    # HERE IS WHERE TO REMOVE IT FROM THE REPEAT LIST
                else:
                    _temp_todo.append(temp_request)
            else:
                continue

        # Now, convert the temporary todo list into an actual one
        # If you implement blocking for bulk operations on the queue, this is
        # when to release it.
        # _temp_todo = sorted(list(_temp_todo)['priority'])
        with self._todo_lock:
            self._todo.extend(_temp_todo)
        with self._tore_lock:
            self._torepeat.extend(_temp_tore)

    def _complete_request(self):
        complete_request(self._my_queue)

    def _order_todo(self):
        pass

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

    def _check_stop(self):
        # Check for any stop flags.
        # The flags themselves are threadsafe. Should I add some thread 
        # protection for stoptask?
        # This is causing issues if there's no lock (the dict is changing
        # during iteration)
        with self.lock:
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

def process_request(channel):
    ''' Turns a request on a channel into a usable format.
    '''
    try:
        command = channel.get(block=False)
    except Empty:
        return None

    if type(channel) is PriorityQueue:
        # Strip out the priority and just grab the dict
        command = command[1]

    return command

def complete_request(channel):
    ''' Notifies a channel of task completion.
    '''
    channel.task_done()

def request_task(target, origin, command, payload, priority=None, 
    repeat=None, *args, **kwargs):
    ''' Puts a request on the queue specified by channel.
    Priority is saturated at [0,1] and 0 represents lowest priority, 1
    represents highest. Don't blame me, blame sorted(). Returns true if 
    successful, false if unsuccessful (indicating queue is full).

    If a return communication is expected, the channel must be specified in 
    payload.

    payload should be tuple of: (list, dict)

    repeat: 
    + None -> schedule once
    + True -> schedule forever
    + False -> unschedule forever
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
        'payload': payload, 'repeat': repeat}

    # Support targeting either a specific queue or a specific PHB
    if type(target) is PointyHairedBoss:
        _target_q = target.get_channel()
    elif type(target) is PriorityQueue:
        item = (_priority, item)
        _target_q = target
    elif type(target) is Queue:
        _target_q = target

    try:
        _target_q.put(item, block=False)
    except queue.Full:
        return False

    return True

def raise_stop_flag(which):
    ''' Wrapper for setting a stop flag. '''
    # Should change this to duck typing
    if type(which) is PointyHairedBoss:
        flag = which.get_stop_flag()
    else:
        flag = which

    flag.set()

if __name__ == '__main__':
    PHB = PointyHairedBoss()
    PHB.run()