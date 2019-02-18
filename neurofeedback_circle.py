import pylsl
from psychopy import event, visual, core
import numpy
import copy
import collections


class test_inlet(pylsl.StreamInlet):

    def __init__(self, max_sec, num = 0, **keyargs):
        streams = pylsl.resolve_byprop('type', 'EEG')
        super().__init__(
            streams[num],
            processing_flags=pylsl.proc_clocksync | pylsl.proc_dejitter | pylsl.proc_monotonize
            )

        self.sample_rate = self.info().nominal_srate()
        self.max_samples = int(max_sec * self.sample_rate)
        data_shape = (self.channel_count, self.max_samples)
        self.data = numpy.nan * numpy.ones(data_shape, dtype=numpy.float32)

    def update(self):
        _, timestamps = self.pull_chunk(max_samples=self.max_samples, dest_obj=self.data)
        # why deepcopy ?
        # why numpinize timestamps ?
        return copy.deepcopy(self.data), numpy.asarray(tiemstamps)


class circular_feedback(visual.Window):
    
    def __init__(self, edges, fillColor, **keyargs):
        super().__init__(**keyargs)
        self.circle = visual.Circle(
            self, edges=edges, fillColor=fillColor, allowGUI=False
            )
    
    def flip(self, radius, **keyargs):
        self.circle.setRadius(radius)
        super().flip(**keyargs)


def fft(time_sequences, sample_rate):
    """
    time_sequences  :must be [[s1,s1,s1,...],[s2,s2,s2,...],...]
    """
    window = numpy.hamming(len(time_sequences[0]))
    windowed_sequences = window * time_sequences
    
    numpy.fft.fft(time_sequences, )

if __name__ == '__main__':
    # for get EEG data
    ## setup buffer
    inlet = test_inlet(1.)
    eeg_buffer = collections.deque(maxlen=inlet.max_samples)

    ## get electrode index
    from get_channel_names import get_channel_names
    ROI_elec_names = 'F3', 'F4'
    channel_names = get_channel_names(inlet.info())
    ROI_elec_indexes = [index for index, name in enumerate(channel_names) if name in elec_name]

    # for display
    ## set stop key
    import sys
    esckey = 'escape'
    event.globalKeys.add(key=esckey, func=sys.exit)

    ## init psychopy
    win = circular_feedback(32, 'green')

    ## set max experiment time
    routine_time = 10
    routine_timer = core.CountdownTimer(routine_time)

    while routine_timer.getTime() > 0:
        # get EEG data
        data, timestamps = inlet.update()
        eeg_buffer.extend(data.T[[ROI_elec_indexes]])
        if len(eeg_buffer) < eeg_buffer.maxlen:
            pass
        # fft
        win.flip()