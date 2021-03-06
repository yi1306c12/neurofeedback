import pylsl
from psychopy import event, visual, core
import numpy
import copy
import collections

from inlet_deque import InletDeque


class test_inlet(pylsl.StreamInlet):

    def __init__(self, num = 0, **keyargs):
        streams = pylsl.resolve_byprop('type', 'EEG')
        super().__init__(
            streams[num],
            processing_flags=pylsl.proc_clocksync | pylsl.proc_dejitter | pylsl.proc_monotonize
            )

        self.sample_rate = self.info().nominal_srate()
#        self.max_samples = int(max_sec * self.sample_rate)
#        data_shape = (self.channel_count, self.max_samples)
#        self.data = numpy.inf * numpy.ones(data_shape, dtype=numpy.float32)

    def update(self):
#        _, timestamps = self.pull_chunk(max_samples=self.max_samples, dest_obj=self.data)
        data, timestamps = self.pull_chunk()#max_samples=self.max_samples)
        # why deepcopy ?
        ## to avoid someone change the self.data.shape
#        return copy.deepcopy(self.data), numpy.asarray(timestamps)
        return numpy.asarray(data), timestamps


class circular_feedback(visual.Window):
    
    def __init__(self, edges, color1, color2, **keyargs):
        super().__init__(**keyargs)
        self.circle1 = visual.Circle(
            self, edges=edges, fillColor=color1, lineColor=color1, pos=(-540,0)
            )
        self.circle2 = visual.Circle(
            self, edges=edges, fillColor=color2, lineColor=color2, pos=(540,0)
            )
    
#    def flip(self, radius, **keyargs):
#        self.circle.setRadius(radius)
#        super().flip(**keyargs)


def wave2psd(waves, sample_rate):
    """
    waves   :must be [[w1_t0, w2_t0, w3_t0, ...], [w1_t1, w2_t1, w3_t1, ...], ...]
    """
    #apply window
    N = len(waves)
    window = numpy.reshape(numpy.hamming(N), (-1, 1))
    windowed_waves = window * numpy.asarray(waves)
#    print(numpy.asarray(waves).shape, window.shape)
    #psds
    Fs = numpy.fft.fftn(windowed_waves, axes=(0,))
    psds = numpy.abs(Fs)**2
    #freq
    freq = numpy.fft.fftfreq(N, d=1./sample_rate)
    return numpy.array_split(psds, 2)[0], numpy.array_split(freq, 2)[0]# return the parts of 0~N/2[Hz]

if __name__ == '__main__':
    max_sec = 1
    # for get EEG data
    stream = pylsl.resolve_byprop('type', 'EEG')[0]
    inlet_deque = InletDeque(
        stream,
        max_sec,
        processing_flags=pylsl.proc_clocksync | pylsl.proc_dejitter | pylsl.proc_monotonize
    )

    ## get electrode index
    from get_channel_names import get_channel_names
    ROI_elec_names = ('F3', 'F4')
    channel_names = get_channel_names(inlet_deque.inlet.info())
    ROI_elec_indexes = [index for index, name in enumerate(channel_names) if name in ROI_elec_names]
    assert len(ROI_elec_names) == len(ROI_elec_indexes), "names:{}, indexes:{}".format(ROI_elec_names,ROI_elec_indexes)

    # for display
    ## set stop key
    import sys
    esckey = 'escape'
    event.globalKeys.add(key=esckey, func=sys.exit)

    ## init psychopy
    win = circular_feedback(128, 'limegreen', 'red', size=[1920, 1080], units='pix', fullscr=True, allowGUI=False)

    ## set max experiment time
    routine_time = int(sys.argv[1])
    routine_timer = core.CountdownTimer(routine_time)

    while routine_timer.getTime() > 0:
        # get EEG data
        data, timestamps = inlet_deque.update()
        assert not numpy.any(numpy.isnan(data)), "data has 'nan' value :{}".format(data)

        if len(timestamps) == 0:
            continue

        # fft
        psds, freq = wave2psd(data[:, ROI_elec_indexes], inlet_deque.sampling_rate)
        amps = psds**0.5

        # display
        band = (8, 12) # alpha band
        r = amps[(band[0] < freq) & (freq < band[1])].mean(axis=0) * 0.1
#        print(len(eeg_buffer), eeg_buffer[0].shape, amps.shape) 
        win.circle1.setRadius(r[0])
        win.circle1.draw()
        win.circle2.setRadius(r[1])
        win.circle2.draw()
        win.flip()
        print(*r)