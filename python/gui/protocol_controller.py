import gtk
import pickle
import time
import os
import matplotlib.pyplot as plt
from protocol import Protocol, FeedbackOptions

def is_float(s):
    try: return (float(s), True)[1]
    except (ValueError, TypeError), e: return False

def check_float(textentry, prev_value):
    val = textentry.get_text()
    if is_float(val):
        return float(val)
    else:
        print "error" # TODO dialog error
        textentry.set_text(str(prev_value))
        return prev_value

def is_int(s):
    try: return (int(s), True)[1]
    except (ValueError, TypeError), e: return False

def check_int(textentry, prev_value):
    val = textentry.get_text()
    if is_int(val):
        return int(val)
    else:
        print "error" # TODO dialog error
        textentry.set_text(str(prev_value))
        return prev_value

class FeedbackOptionsDialog:
    def __init__(self, options):
        builder = gtk.Builder()
        builder.add_from_file(os.path.join("gui",
                                           "glade",
                                           "feedback_options_dialog.glade"))
        self.dialog = builder.get_object("feedback_options_dialog")
        self.options = options
        self.textentry_sampling_time_ms = \
            builder.get_object("textentry_sampling_time_ms")
        self.textentry_n_samples = \
            builder.get_object("textentry_n_samples")
        self.textentry_delay_between_samples_ms = \
            builder.get_object("textentry_delay_between_samples_ms")

        self.textentry_sampling_time_ms.set_text(str(options.sampling_time_ms))
        self.textentry_n_samples.set_text(str(options.n_samples))
        self.textentry_delay_between_samples_ms.set_text(
                                         str(options.delay_between_samples_ms))
        
    def run(self):
        response = self.dialog.run()
        if response == gtk.RESPONSE_OK:
            self.options.sampling_time_ms = \
                check_int(self.textentry_sampling_time_ms,
                          self.options.sampling_time_ms)
            self.options.n_samples = \
                check_int(self.textentry_n_samples,
                          self.options.n_samples)
            self.options.delay_between_samples_ms = \
                check_int(self.textentry_delay_between_samples_ms,
                          self.options.delay_between_samples_ms)
        self.dialog.hide()
        return response

class ProtocolController():
    def __init__(self, app, builder, signals):
        self.app = app
        self.is_running = False
        self.file_name = None
        self.previous_voltage = None
        self.previous_frequency = None
        self.button_first_step = builder.get_object("button_first_step")
        self.button_prev_step = builder.get_object("button_prev_step")
        self.button_next_step = builder.get_object("button_next_step")
        self.button_last_step = builder.get_object("button_last_step")
        self.button_insert_step = builder.get_object("button_insert_step")
        self.button_delete_step = builder.get_object("button_delete_step")
        self.button_run_protocol = builder.get_object("button_run_protocol")
        self.button_feedback_options = builder.get_object("button_feedback_options")
        self.label_step_number = builder.get_object("label_step_number")
        self.menu_save_protocol = builder.get_object("menu_save_protocol")
        self.menu_save_protocol_as = builder.get_object("menu_save_protocol_as")
        self.menu_load_protocol = builder.get_object("menu_load_protocol")
        self.menu_add_frequency_sweep = builder.get_object("menu_add_frequency_sweep")
        self.menu_add_electrode_sweep = builder.get_object("menu_add_electrode_sweep")
        self.textentry_voltage = builder.get_object("textentry_voltage")
        self.textentry_frequency = builder.get_object("textentry_frequency")
        self.textentry_step_time = builder.get_object("textentry_step_time")
        self.checkbutton_feedback = builder.get_object("checkbutton_feedback")
        self.image_play = builder.get_object("image_play")
        self.image_pause = builder.get_object("image_pause")

        signals["on_button_insert_step_clicked"] = self.on_insert_step
        signals["on_button_delete_step_clicked"] = self.on_delete_step
        signals["on_button_first_step_clicked"] = self.on_first_step
        signals["on_button_prev_step_clicked"] = self.on_prev_step
        signals["on_button_next_step_clicked"] = self.on_next_step
        signals["on_button_last_step_clicked"] = self.on_last_step
        signals["on_button_run_protocol_clicked"] = self.on_run_protocol
        signals["on_button_feedback_options_clicked"] = self.on_feedback_options
        signals["on_menu_new_protocol_activate"] = self.on_new_protocol
        signals["on_menu_save_protocol_activate"] = self.on_save_protocol
        signals["on_menu_save_protocol_as_activate"] = self.on_save_protocol_as
        signals["on_menu_load_protocol_activate"] = self.on_load_protocol
        signals["on_menu_add_frequency_sweep_activate"] = self.on_add_frequency_sweep
        signals["on_menu_add_electrode_sweep_activate"] = self.on_add_electrode_sweep
        signals["on_textentry_voltage_focus_out_event"] = \
                self.on_textentry_voltage_focus_out
        signals["on_textentry_voltage_key_press_event"] = \
                self.on_textentry_voltage_key_press
        signals["on_textentry_frequency_focus_out_event"] = \
                self.on_textentry_frequency_focus_out
        signals["on_textentry_frequency_key_press_event"] = \
                self.on_textentry_frequency_key_press
        signals["on_textentry_step_time_focus_out_event"] = \
                self.on_textentry_step_time_focus_out
        signals["on_textentry_step_time_key_press_event"] = \
                self.on_textentry_step_time_key_press
        signals["on_checkbutton_feedback_toggled"] = \
                self.on_feedback_toggled

    def on_insert_step(self, widget, data=None):
        self.app.protocol.insert_step()
        self.app.main_window_controller.update()

    def on_delete_step(self, widget, data=None):
        self.app.protocol.delete_step()
        self.app.main_window_controller.update()

    def on_first_step(self, widget=None, data=None):
        self.app.protocol.first_step()
        self.app.main_window_controller.update()

    def on_prev_step(self, widget=None, data=None):
        self.app.protocol.prev_step()
        self.app.main_window_controller.update()

    def on_next_step(self, widget=None, data=None):
        self.app.protocol.next_step()
        self.app.main_window_controller.update()

    def on_last_step(self, widget=None, data=None):
        self.app.protocol.last_step()
        self.app.main_window_controller.update()

    def on_new_protocol(self, widget, data=None):
        self.file_name = None
        self.app.protocol = Protocol()
        self.app.main_window_controller.update()

    def on_save_protocol(self, widget, data=None):
        if self.file_name:
            output = open(self.file_name, 'wb')
            pickle.dump(self.app.protocol, output, -1)
            output.close()
        else:
            self.on_save_protocol_as(widget, data)

    def on_save_protocol_as(self, widget, data=None):
        dialog = gtk.FileChooserDialog(title=None,
                                       action=gtk.FILE_CHOOSER_ACTION_SAVE,
                                       buttons=(gtk.STOCK_CANCEL,
                                                gtk.RESPONSE_CANCEL,
                                                gtk.STOCK_SAVE_AS,
                                                gtk.RESPONSE_OK))
        dialog.set_default_response(gtk.RESPONSE_OK)
        dialog.set_current_folder("protocols")
        dialog.set_current_name("new")
        response = dialog.run()
        if response == gtk.RESPONSE_OK:
            self.file_name = dialog.get_filename()
            output = open(self.file_name, 'wb')
            pickle.dump(self.app.protocol, output, -1)
            output.close()
        dialog.destroy()

    def on_load_protocol(self, widget, data=None):
        dialog = gtk.FileChooserDialog(title=None,
                                       action=gtk.FILE_CHOOSER_ACTION_OPEN,
                                       buttons=(gtk.STOCK_CANCEL,
                                                gtk.RESPONSE_CANCEL,
                                                gtk.STOCK_OPEN,
                                                gtk.RESPONSE_OK))
        dialog.set_default_response(gtk.RESPONSE_OK)
        dialog.set_current_folder("protocols")
        response = dialog.run()
        if response == gtk.RESPONSE_OK:
            self.file_name = dialog.get_filename()
            f = open(self.file_name, 'rb')
            self.app.protocol = pickle.load(f)
            f.close()
        dialog.destroy()
        self.app.main_window_controller.update()

    def on_add_frequency_sweep(self, widget, data=None):
        print "add frequency sweep"

    def on_add_electrode_sweep(self, widget, data=None):
        print "add electrode sweep"

    def on_textentry_step_time_focus_out(self, widget, data=None):
        self.on_step_time_changed()

    def on_textentry_step_time_key_press(self, widget, event):
        if event.keyval == 65293: # user pressed enter
            self.on_step_time_changed()

    def on_step_time_changed(self):        
        self.app.protocol.current_step().time = \
            check_int(self.textentry_step_time,
                      self.app.protocol.current_step().time)

    def on_textentry_voltage_focus_out(self, widget, data=None):
        self.on_voltage_changed()

    def on_textentry_voltage_key_press(self, widget, event):
        if event.keyval == 65293: # user pressed enter
            self.on_voltage_changed()

    def on_voltage_changed(self):
        self.app.protocol.current_step().voltage = \
            check_int(self.textentry_voltage,
                      self.app.protocol.current_step().voltage)
        self.update()
        
    def on_textentry_frequency_focus_out(self, widget, data=None):
        self.on_frequency_changed()

    def on_textentry_frequency_key_press(self, widget, event):
        if event.keyval == 65293: # user pressed enter
            self.on_frequency_changed()

    def on_frequency_changed(self):
        self.app.protocol.current_step().frequency = \
            check_float(self.textentry_frequency,
                        self.app.protocol.current_step().frequency/1e3)*1e3
        self.update()

    def on_feedback_toggled(self, widget, data=None):
        if self.checkbutton_feedback.get_active():
            if self.app.protocol.current_step().feedback_options is None:
                self.app.protocol.current_step().feedback_options = \
                    FeedbackOptions()
            self.button_feedback_options.set_sensitive(True)
            self.textentry_step_time.set_sensitive(False)
        else:
            self.app.protocol.current_step().feedback_options = None
            self.button_feedback_options.set_sensitive(False)
            self.textentry_step_time.set_sensitive(True)
            
    def on_run_protocol(self, widget, data=None):
        if self.is_running:
            self.is_running = False
            self.button_run_protocol.set_image(self.image_play)
        else:
            self.is_running = True
            self.button_run_protocol.set_image(self.image_pause)
            self.run_step()

    def on_feedback_options(self, widget, data=None):
        FeedbackOptionsDialog(self.app.protocol.current_step().feedback_options).run()
        self.app.main_window_controller.update()

    def run_step(self):
        self.app.main_window_controller.update()
        while gtk.events_pending():
            gtk.main_iteration()
        if self.app.control_board.connected():
            feedback_options = \
                self.app.protocol.current_step().feedback_options
            state = self.app.protocol.current_step().state_of_channels
            if feedback_options:
                impedance = self.app.control_board.MeasureImpedance(
                           feedback_options.sampling_time_ms,
                           feedback_options.n_samples,
                           feedback_options.delay_between_samples_ms,
                           state)
            else:
                self.app.control_board.set_state_of_all_channels(state)
                time.sleep(self.app.protocol.current_step().time/1000.0)
        else:
                time.sleep(self.app.protocol.current_step().time/1000.0)

        if self.app.protocol.current_step_number < len(self.app.protocol)-1 and self.is_running:
            self.app.protocol.next_step()
            self.run_step()
        else:
            self.is_running = False
            self.button_run_protocol.set_image(self.image_play)
        return False

    def update(self):
        self.textentry_step_time.set_text(str(self.app.protocol.current_step().time))
        self.textentry_voltage.set_text(str(self.app.protocol.current_step().voltage))
        self.textentry_frequency.set_text(str(self.app.protocol.current_step().frequency/1e3))
        self.label_step_number.set_text("Step: %d/%d" % 
            (self.app.protocol.current_step_number+1, len(self.app.protocol.steps)))

        # if this step has feedback enabled
        if self.app.protocol.current_step().feedback_options:
            self.checkbutton_feedback.set_active(True)
        else:
            self.checkbutton_feedback.set_active(False)

        if self.app.control_board.connected() and \
            (self.app.realtime_mode or self.is_running):
            if self.app.func_gen:
                self.app.func_gen.set_voltage(self.app.protocol.current_step().voltage)
                self.app.func_gen.set_frequency(self.app.protocol.current_step().frequency)
            else:
                self.app.control_board.set_actuation_voltage(float(self.app.protocol.current_step().voltage))
                self.app.control_board.set_actuation_frequency(float(self.app.protocol.current_step().frequency))
            if self.is_running is False:
                state = self.app.protocol.state_of_all_channels()
                self.app.control_board.set_state_of_all_channels(state)