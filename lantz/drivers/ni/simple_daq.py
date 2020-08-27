from lantz.core import Action, Driver, Q_

from lantz.drivers.ni.daqmx import AnalogInputTask, CountEdgesChannel, CounterInputTask, Device, VoltageInputChannel


class Read_DAQ(Driver):
    """
    This is a simplified version of a daq drivers which can be used when where only standard read on the daq is necessary
    """

    def __init__(self, device_name):
        self._daq = Device(device_name)
        self._tasks = dict()

    @Action()
    def new_task(self, task_name, channels):
        """
        task_name must be unique on the device
        channels is a list of channels to be included in the task (eg ['Dev1/ctr2', 'Dev1/ctr3'])
        """
        if task_name in self._tasks:
            self.clear_task(task_name)
        ch0 = channels[0]
        if ch0 in self._daq.counter_input_channels:
            task = CounterInputTask(task_name)
            task_type = 'counter'
            valid_channels = self._daq.counter_input_channels
        elif ch0 in self._daq.analog_input_channels:
            task = AnalogInputTask(task_name)
            task_type = 'analog'
            valid_channels = self._daq.analog_input_channels
        else:
            raise Exception(
                'Cannot identify the type of channel for {}. Channel must be either in {}, or in {}'.format(ch0,
                                                                                                            self._daq.counter_input_channels,
                                                                                                            self._daq.analog_input_channels))

        for ch in channels:
            if ch in valid_channels:
                ch_obj = CountEdgesChannel(ch) if task_type == 'counter' else VoltageInputChannel(ch)
                task.add_channel(ch_obj)
            else:
                task.clear()
                raise Exception('Invalid channel {} for task of type {}'.format(ch, task_type))

        self._tasks[task_name] = task

    @Action()
    def clear_task(self, task_name):
        task = self._tasks.pop(task_name)
        task.clear()

    @Action()
    def clear_all_task(self):
        for task_name in self._tasks:
            self.clear_task(task_name)

    @Action()
    def start(self, task_name):
        self._tasks[task_name].start()

    @Action()
    def stop(self, task_name):
        self._tasks[task_name].stop()

    @Action()
    def read(self, task_name, samples_per_channel=None, timeout=Q_(10.0, 's'), group_by='channel'):
        task = self._tasks[task_name]
        if task.IO_TYPE == 'AI':
            return task.read(samples_per_channel=samples_per_channel, timeout=timeout, group_by=group_by)
        elif task.IO_TYPE == 'CI':
            return task.read(samples_per_channel=samples_per_channel, timeout=timeout)

    @Action()
    def configure_timing_sample_clock(self, task_name, **kwargs):
        return self._tasks[task_name].configure_timing_sample_clock(**kwargs)

    @Action()
    def get_task_type(self, task_name):
        return self._tasks[task_name].IO_TYPE

    # def simple_read
    #     if self.task.IO_TYPE == 'AI':
    #         self.task.read(samples_per_channel=samples)
    #     elif self.task.IO_TYPE == 'CI':

    #     else:
    #         raise Exception('Unkown IO_TYPE of {}'.format(self.task.IO_TYPE))
