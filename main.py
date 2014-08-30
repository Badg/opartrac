from kivy.app import App
from kivy.clock import Clock
import os
from gui import *
import sys
sys.path.append('../')
from threading import Thread
import threading
from queue import Queue, Empty
import time

import control

import pymphys as phz
import nodepandas as pdn

class OpartracApp(App):
    def __init__(self, name, *args, **kwargs):
        # Keep track of this process' name
        self.__name = name
        # Create a slave PHB to interface with control
        self._phb = control.PointyHairedBoss(self.__name, slave=True)

        # # Get the commander
        # self.commander = commander
        # # Register the queue to communicate with commander
        # self.channel = self.commander.get_channel(self.nametag)
        # # Register the commander event to flag when App exits
        # # Probably unnecessary, as it would be preferred to use 
        # #     self.control.raise_stop_flag(self.nametag)
        # self.stop_flag = self.commander.get_stop_flag(self.nametag)
        # # Get the queue for the commanding officer
        # self.CO_channel = self.commander.get_channel(None)
        # # Register what commands mean what
        # self.tasks = {'print': print, 'preview': self.select_data}

        # Call the superdupersuperman!
        super(OpartracApp, self).__init__(**kwargs)

        # Schedule the slave to run every little bit
        self._control_interval = 1/60.0
        Clock.schedule_interval(self._phb.run_once, self._control_interval)

    def get_interface(self):
        return self._phb

    def task_check(self, *args, **kwargs):
        task = control.poll_requests(self.channel)
        if task:
            # Dispatch the task based on the self.tasks dict
            self.tasks[task['command']](task['payload'])
            control.done_task(self.channel)


    def build(self):
        # Create the base UI manager
        self.base = UIManager(self)

        # Add the dataloader to the base UI manager's primary layout
        self.base.add_component("dataloader", DataLoader())

        # Build the base UI manager
        return self.base

    def select_data(self, path, filename):
        self.base.data_selected = True

        # Join the loader bits (temporarily disabled for development)
        # _filename = os.path.join(path, filename[0])
        _filename = "./comsol_sample/finer.txt"
        headerlines, headers, colspecs, previewdata, fields, units = \
            pdn.io.load_mphtxt(_filename)

        # Bring in the relevant bits to self
        self._sourcefile = {"filename": _filename, "headers": headerlines, 
            "colspecs": colspecs, "fields": fields, "units": units}
        
        # Turn the header list into a string
        headertxt = ""
        for line in headers:
            headertxt += line + "\n"
        headertxt = headertxt.strip('\n')

        # Decide which fields might be coordinates
        coords_to_check = ['x', 'y', 'z']

        previews = {}
        previews["headers"] = headertxt
        previews["labels"] = fields
        previews["data"] = previewdata
        previews["units"] = units
        previews["coords"] = [field in coords_to_check for field in fields]

        self.base.preview_imported_data(previews)

    def set_fields(self, fields):
        self._sourcefile["fields"] = fields

    def set_units(self, units):
        self._sourcefile["units"] = units

    def set_coords(self, coords):
        self._sourcefile["coords"] = coords

    def do_import(self):
        columns = self._sourcefile["fields"]
        coords = self._sourcefile["coords"]
        units = self._sourcefile["units"]

        rawdf = pdn.io.import_mphtxt(self._sourcefile["filename"], 
            self._sourcefile["headers"], self._sourcefile["colspecs"], 
            columns, units=units, coords=coords)
        print(rawdf)

    def on_stop(self):
        # The Kivy event loop is about to stop, set a stop signal;
        # otherwise the app window will close, but the Python process will
        # keep running until all secondary threads exit.
        control.raise_stop_flag(self._phb)

def shout(instance, target):
    ''' Generic function to test communication between two nodes and request
    execution.
    '''
    success = instance.make_request(target, 'print', 
        (["Look at me, PHB, running 'round the Christmas tree!"], {}))
    time.sleep(1)

def main():
    # Create control (too bad kivy needs to be in the main thread)
    _bossman = control.PointyHairedBoss(name="control", tasks={})
    _bossman.add_task('shout', shout)

    # Define what to call the gui
    _guiname = "gui"
    # Create the gui app
    _gui = OpartracApp(_guiname)
    _gui_phb = _gui.get_interface()
    _gui_phb.add_task('print', print)

    # Connect the gui slave PHB to control
    _bossman.link_phb(_gui_phb)

    # Ask _bossman to repeatedly shout at the GUI (thanks, god)
    control.request_task(_bossman, 'god', 'shout', ([_bossman, _gui_phb], {}), 
        repeat=True)

    # Run the app.
    _gui.run()

if __name__ == '__main__':
    main()