from copy import deepcopy
import numpy as np

class FeedbackOptions():
    def __init__(self, sampling_time_ms=None,
                 n_samples=None,
                 delay_between_samples_ms=None):
        if sampling_time_ms:
            self.sampling_time_ms = sampling_time_ms
        else:
            self.sampling_time_ms = 10
        if n_samples:
            self.n_samples = n_samples
        else:
            self.n_samples = 10
        if delay_between_samples_ms:
            self.delay_between_samples_ms = delay_between_samples_ms
        else:
            self.delay_between_samples_ms = 0
             
class Step():
    def __init__(self, n_channels, time=None, voltage=None,
                 frequency=None, feedback_options=None):
        if time:
            self.time = time
        else:
            self.time = 100
        if voltage:
            self.voltage = voltage
        else:
            self.voltage = 100
        if frequency:
            self.frequency = frequency
        else:
            self.frequency = 1e3
        if feedback_options:
            self.feedback_options = deepcopy(feedback_options)
        else:
            self.feedback_options = None
        self.n_channels = n_channels
        self.state_of_channels = np.zeros(n_channels)

class Protocol():
    def __init__(self, n_channels=None):
        if n_channels:
            self.n_channels = n_channels
        else:
            self.n_channels = 40
        self.current_step_number = 0
        self.steps = [Step(self.n_channels)]

    def __len__(self):
        return len(self.steps)

    def set_state_of_channel(self, index, state):
        self.current_step().state_of_channels[index] = state

    def state_of_all_channels(self):
        return self.current_step().state_of_channels

    def current_step(self):
        return self.steps[self.current_step_number]

    def insert_step(self):
        self.steps.insert(self.current_step_number,
                          Step(self.n_channels,
                               self.current_step().time,
                               self.current_step().voltage,
                               self.current_step().frequency,
                               self.current_step().feedback_options))

    def delete_step(self):
        if len(self.steps) > 1:
            del self.steps[self.current_step_number]
            if self.current_step_number == len(self.steps):
                self.current_step_number -= 1
        else: # reset first step
            self.steps = [Step(self.n_channels)]

    def next_step(self):
        if self.current_step_number == len(self.steps)-1:
            self.steps.append(Step(self.n_channels,
                                   self.current_step().time,
                                   self.current_step().voltage,
                                   self.current_step().frequency,
                                   self.current_step().feedback_options))
        self.goto_step(self.current_step_number+1)
            
    def prev_step(self):
        if self.current_step_number > 0:
            self.goto_step(self.current_step_number-1)

    def first_step(self):
        self.goto_step(0)

    def last_step(self):
        self.goto_step(len(self.steps)-1)

    def goto_step(self, step):
        self.current_step_number = step