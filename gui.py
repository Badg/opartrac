from kivy.uix.widget import Widget
from kivy.uix.popup import Popup
from kivy.uix.label import Label
from kivy.uix.textinput import TextInput
from kivy.uix.stacklayout import StackLayout
from kivy.uix.boxlayout import BoxLayout
from kivy.properties import NumericProperty, ReferenceListProperty, \
    ObjectProperty, StringProperty, BooleanProperty, ListProperty
from kivy.vector import Vector
from kivy.clock import Clock
from random import randint
from kivy.uix.tabbedpanel import TabbedPanel
from kivy.uix.floatlayout import FloatLayout
from kivy.animation import Animation
from kivy.factory import Factory
import os
import copy
import time

class DataLoader(Widget):
    def __init__(self, **kwargs):
        super(DataLoader, self).__init__(**kwargs)

class UIManager(Widget):
    """ Root widget for the app. Handles creation and destruction of widgets.
    """

    # Get the layout widgets
    layout = ObjectProperty(None)
    dataloader = ObjectProperty(None)
    getdata = ObjectProperty(None)
    processdata = ObjectProperty(None)
    vizdata = ObjectProperty(None)
    savedatagen = ObjectProperty(None)
    uiroot = ObjectProperty(None)
    loader_acc = ObjectProperty(None)
    loader_acc_ver = ObjectProperty(None)
    loader_acc_sel = ObjectProperty(None)
    loader_acc_disp = ObjectProperty(None)
    loader_preview_grid = ObjectProperty(None)

    # State control variables
    data_selected = BooleanProperty(False)
    imported_header = StringProperty('')
    loader_preview_cols = NumericProperty(1)
    loader_preview_rows = NumericProperty(1)

    # User-available fields
    labels = ListProperty([])
    units = ListProperty([])
    coords = ListProperty([])
    types = ListProperty([])

    # Override the init 
    def __init__(self, app_control, **kwargs):
        super(UIManager, self).__init__(**kwargs)

        # Create the dictionary for available dynamic components
        self.components = {}
        self.control = app_control

    def add_component(self, comp_id, component):
        """ Adds a dynamic component, to be served later."""
        self.components[comp_id] = component

    def serve_component(self, comp_id, target=None):
        """ Makes a dynamic component visible to the user, if not already."""
        # Check to see that it doesn't already have a parent (not yet added)
        if not self.components[comp_id].parent:
            if target:
                target.add_widget(self.components[comp_id])
            else:
                self.add_widget(self.components[comp_id])

    def destroy_component(self, comp_id=None, target=None):
        """ Hides a dynamic component from the user."""
        # Make sure only one input is defined
        if not (bool(comp_id) != bool(target)):
            raise ValueError("Please define a component ID xor a target.")

        if comp_id and self.components[comp_id].parent:
            self.components[comp_id].parent.remove_widget(
                self.components[comp_id])
        elif target and target.parent:
            target.parent.remove_widget(target)

    def preview_imported_data(self, previews):
        # Update the preview grid size
        self.loader_preview_cols = len(previews["data"][0])
        self.loader_preview_rows = len(previews["data"]) + 1

        # Update the upper description
        self.imported_header = 'File description:\n' + previews["headers"]

        # Clear the preview grid (if data has been reloaded or summat)
        self.loader_preview_grid.clear_widgets()

        # Update the "labels" and "units" list properties
        self.labels = previews["labels"]
        self.units = previews["units"]
        self.coords = previews["coords"]

        # Populate the preview grid fields and units and stuff.
        for ii in range(len(self.labels)):
            thislayout = BoxLayout(orientation='vertical', 
                size_hint=[1, None])
            descwidget = MinTextInput(text=self.labels[ii], height=20,
                font_size=15, hint_text='Field name')

            thislayout.add_widget(descwidget)
            # Gotcha: late-binding closures in this lambda
            descwidget.bind(text=lambda instance, value, ii=ii: \
                self.update_label(ii, value))
            unitwidget = MinTextInput(text=self.units[ii], height=25,
                font_size=15, hint_text='Units')
            thislayout.add_widget(unitwidget)
            # Gotcha: late-binding closures in this lambda
            unitwidget.bind(text=lambda instance, value, ii=ii: \
                self.update_units(ii, value))
            coordwidget = CoordConf(height=20)
            coordwidget.children[0].active = self.coords[ii]
            coordwidget.children[0].bind(active=lambda instance, value, ii=ii: \
                self.make_coord(ii, value))

            #coordwidget.bind(height=max([child.height for child in 
            #    self.children]))

            thislayout.add_widget(coordwidget)

            thislayout.height = sum([child.height for child in 
                thislayout.children])
            self.loader_preview_grid.add_widget(thislayout)

        # Populate the preview grid values
        for line in previews["data"]:
            for item in line:
                self.loader_preview_grid.add_widget(MinLabel(text=item))

        # Focus on the appropriate accordion item
        self.loader_acc.select(self.loader_acc_imp)

    def update_label(self, whichone, value):
        self.labels[whichone] = value

    def update_units(self, whichone, value):
        self.units[whichone] = value

    def make_coord(self, whichone, value):
        self.coords[whichone] = value

    def trigger_data_import(self):
        load_pop_label = Label(text='Now loading file. Please be patient; this '
            'may take some time.', size_hint=(None, None), 
            text_size=(190, 190), valign='middle', halign='center')
        loading_popup = Popup(title='Loading', size_hint=(None, None), 
            size=(300, 200), auto_dismiss=False, content=load_pop_label)
        load_pop_label.size = loading_popup.size
        loading_popup.open()
        self.control.set_coords(self.coords)
        self.control.set_fields(self.labels)
        self.control.set_units(self.units)
        # Wait for the popup to open, then import
        Clock.schedule_once((lambda __trash__: self.control.do_import()), 0)
        loading_popup.dismiss()

class CoordConf(Widget):
    pass

class TabPanelSwag(TabbedPanel):

    #override tab switching method to animate on tab switch
    def switch_to(self, header):
        anim = Animation(opacity=0, d=.24, t='in_out_quad')

        def start_anim(_anim, child, in_complete, *lt):
            _anim.start(child)

        def _on_complete(*lt):
            if header.content:
                header.content.opacity = 0
                anim = Animation(opacity=1, d=.43, t='in_out_quad')
                start_anim(anim, header.content, True)
            super(TabPanelSwag, self).switch_to(header)

        anim.bind(on_complete=_on_complete)
        if self.current_tab.content:
            start_anim(anim, self.current_tab.content, False)
        else:
            _on_complete()

class MinLabel(Label):
    pass

class MinTextInput(TextInput):
    pass

class LoadDialog(FloatLayout):
    # References to buttons and things?
    load = ObjectProperty(None)

    # Internal properties
    file_filters = ListProperty([])
    ref_path = StringProperty('')

    # Set the internal properties
    file_filters = ['*.txt', '*.hd5', '*.hdf5']
    ref_path = '/'