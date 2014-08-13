from kivy.app import App
import os
from gui import *
import sys
sys.path.append('../')
import pymphys as phz
import phynum as phn

class OpartracApp(App):
    def __init__(self, **kwargs):
        super(OpartracApp, self).__init__(**kwargs)

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
            phz.io.load_mphtxt(_filename)

        # Bring in the relevant bits to self
        self._sourcefile = _filename, headerlines, colspecs, fields, units
        
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
        self.fields = fields

    def set_units(self, units):
        self.units = units

    def set_coords(self, coords):
        self.coords = coords

    def do_import(self):
        mphfile, headerlines, colspecs, fields, units = self._sourcefile

        rawdf = phz.io.import_mphtxt(
            mphfile, headerlines, colspecs, fields, units=None)
        print(rawdf)

if __name__ == '__main__':
    OpartracApp().run()