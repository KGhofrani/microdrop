"""
Copyright 2011 Ryan Fobel

This file is part of Microdrop.

Microdrop is free software: you can redistribute it and/or modify
it under the terms of the GNU General Public License as published by
the Free Software Foundation, either version 3 of the License, or
(at your option) any later version.

Microdrop is distributed in the hope that it will be useful,
but WITHOUT ANY WARRANTY; without even the implied warranty of
MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
GNU General Public License for more details.

You should have received a copy of the GNU General Public License
along with Microdrop.  If not, see <http://www.gnu.org/licenses/>.
"""

import os
import shutil

import gtk

from dmf_device import DmfDevice, load as load_dmf_device
from protocol import Protocol, load as load_protocol
from plugin_manager import IPlugin, SingletonPlugin, ExtensionPoint, \
    implements, emit_signal


class ConfigController(SingletonPlugin):
    implements(IPlugin)
        
    def __init__(self):
        self.name = "microdrop.gui.config_controller"
        builder = gtk.Builder()
        builder.add_from_file(os.path.join("gui",
                              "glade",
                              "new_dialog.glade"))
        self.new_dialog = builder.get_object("new_dialog")
        self.new_dialog.textentry = builder.get_object("textentry")
        self.new_dialog.label = builder.get_object("label")

    def on_app_init(self, app):
        self.app = app
        app.config_controller = self

    def on_app_exit(self):
        # TODO: prompt to save if these have been changed 
        self.save_dmf_device()
        self.save_protocol()
        self.app.config.save()
        
    def process_config_file(self):
        # save the protocol name from the config file because it is
        # automatically overwritten when we load a new device
        protocol_name = self.app.config.protocol_name
        self.load_dmf_device()
        # reapply the protocol name to the config file
        self.app.config.protocol_name = protocol_name
        self.load_protocol()

    def dmf_device_name_dialog(self, old_name=None):
        self.new_dialog.set_title("Save device")
        self.new_dialog.label.set_text("Device name:")
        if old_name:
            self.new_dialog.textentry.set_text(old_name)
        else:
            self.new_dialog.textentry.set_text("")
        self.new_dialog.set_transient_for(self.app.main_window_controller.view)
        response = self.new_dialog.run()
        self.new_dialog.hide()
        name = ""
        if response == gtk.RESPONSE_OK:
            name = self.new_dialog.textentry.get_text()
        return name
    
    def protocol_name_dialog(self, old_name=None):
        self.new_dialog.set_title("Save protocol")
        self.new_dialog.label.set_text("Protocol name:")
        if old_name:
            self.new_dialog.textentry.set_text(old_name)
        else:
            self.new_dialog.textentry.set_text("")
        self.new_dialog.set_transient_for(self.app.main_window_controller.view)
        response = self.new_dialog.run()
        self.new_dialog.hide()
        name = ""
        if response == gtk.RESPONSE_OK:
            name = self.new_dialog.textentry.get_text()
        return name

    def save_dmf_device(self, save_as=False, rename=False):
        # if the device has no name, try to get one
        if save_as or rename or self.app.dmf_device.name is None:
            # if the dialog is canceled, name = ""
            name = self.dmf_device_name_dialog(self.app.dmf_device.name)
        else:
            name = self.app.dmf_device.name

        if name:
            # current file name
            if self.app.dmf_device.name:
                src = os.path.join(self.app.config.dmf_device_directory,
                                   self.app.dmf_device.name)
            dest = os.path.join(self.app.config.dmf_device_directory,name)

            # if we're renaming, move the old directory
            if rename and os.path.isdir(src):
                if src == dest:
                    return
                if os.path.isdir(dest):
                    self.app.main_window_controller.error("A device with that "
                        "name already exists.")
                    return
                shutil.move(src, dest)

            if os.path.isdir(dest) == False:
                os.mkdir(dest)

            # save the device            
            self.app.dmf_device.name = name
            self.app.dmf_device.save(os.path.join(dest,"device"))
            
            # update config
            self.app.config.dmf_device_name = name
            self.app.main_window_controller.update()
        
    def save_protocol(self, save_as=False, rename=False):
        if self.app.dmf_device.name:
            if save_as or rename or self.app.protocol.name is None:
                # if the dialog is canceled, name = ""
                name = self.protocol_name_dialog(self.app.protocol.name)
            else:
                name = self.app.protocol.name

            if name:
                path = os.path.join(self.app.config.dmf_device_directory,
                                    self.app.dmf_device.name,
                                    "protocols")
                if os.path.isdir(path) == False:
                    os.mkdir(path)

                # current file name
                if self.app.protocol.name:
                    src = os.path.join(path,self.app.protocol.name)
                dest = os.path.join(path,name)
                self.app.protocol.name = name

                # if we're renaming
                if rename and os.path.isfile(src):
                    shutil.move(src, dest)
                else: # save the file
                    emit_signal("on_protocol_save")
                    self.app.protocol.save(dest)
    
                # update config
                self.app.config.protocol_name = name
                self.app.main_window_controller.update()
    
    def load_dmf_device(self):
        dmf_device = None

        # try what's specified in config file
        if self.app.config.dmf_device_name:
            path = os.path.join(self.app.config.dmf_device_directory,
                                self.app.config.dmf_device_name,
                                "device")
            try:
                emit_signal("on_dmf_device_changed", load_dmf_device(path))
            except:
                self.app.main_window_controller.error("Could not open %s" % path)

        # otherwise, return a new object
        if dmf_device==None:
            dmf_device = DmfDevice()
    
    
    def load_protocol(self):
        protocol = None
        # try what's specified in config file
        if self.app.config.protocol_name:
            path = os.path.join(self.app.config.dmf_device_directory,
                                self.app.config.dmf_device_name,
                                "protocols",
                                self.app.config.protocol_name)
            try:
                protocol = load_protocol(path)
                for (name, (version, data)) in protocol.plugin_data.items():
                    emit_signal("on_protocol_load", [version, data])
            except:
                self.app.main_window_controller.error("Could not open %s" % path)

        # otherwise, return a new object
        if protocol==None:
            protocol = Protocol(self.app.dmf_device.max_channel()+1)
        emit_signal("on_protocol_changed", protocol)
                
    def on_dmf_device_changed(self, dmf_device):
        self.app.config.dmf_device_name = dmf_device.name
        
    def on_protocol_changed(self, protocol):
        self.app.config.protocol_name = protocol.name