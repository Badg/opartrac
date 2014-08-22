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
    def __init__(self, name, control, *args, **kwargs):
        # Keep track of this process' name
        self.nametag = name

        # Get the controller
        self.control = control
        # Register the queue to communicate with controller
        self.q = self.control.get_queue(self.nametag)
        # Register the controller event to flag when App exits
        # Probably unnecessary, as it would be preferred to use 
        #     self.control.raise_stop_flag(self.nametag)
        self.stop_flag = self.control.get_stop_flag(self.nametag)
        # Get the queue for requests of command
        self.commander_q = self.control.get_channel()
        # Register what commands mean what
        self.commands = {'print': print}

        # Call the superdupersuperman!
        super(OpartracApp, self).__init__(**kwargs)

        # Seconds of interval between checking the queue from control
        self.control_refresh_interval = 1/60.0
        Clock.schedule_interval(self.refresh_channel, 
            self.control_refresh_interval)

    def refresh_channel(self, *args, **kwargs):
        if not self.q.empty():
            try:
                command = self.q.get(block=False)
                self.process_command(command)
                self.q.task_done()
            except Empty:
                pass

    def process_command(self, command):
        ''' Pretty dumb method, for the time being. But it'll get the job done
        and can be replaced later.
        '''
        # Pull out the priority
        priority, command = command
        origin, command, payload = command
        print(payload)

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
        self.stop_flag.set()

def main():
    # Define what I'm calling myself
    _selfname = "gui"
    # Create my controller (too bad kivy needs to be in the main thread)
    phb = control.spawn_PHB(name="control", caller=_selfname)

    # Run the app, passing it the controller.
    OpartracApp(_selfname, control=phb).run()

if __name__ == '__main__':
    main()