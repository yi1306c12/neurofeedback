import pylsl
from psychopy import event, visual, core
import numpy
import copy
import collections


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
    
    def __init__(self, edges, color, **keyargs):
        super().__init__(**keyargs)
        self.circle = visual.Circle(
            self, edges=edges, fillColor=color, lineColor=color
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
    #psds
    Fs = numpy.fft.fftn(windowed_waves, axes=(0,))
    psds = numpy.abs(Fs)**2
    #freq
    freq = numpy.fft.fftfreq(N, d=1./sample_rate)
    return numpy.array_split(psds, 2)[0], numpy.array_split(freq, 2)[0]# return the parts of 0~N/2[Hz]

if __name__ == '__main__':
    # for get EEG data
    ## setup buffer
    inlet = test_inlet()
    max_sec = 1
    eeg_buffer = collections.deque(maxlen=int(inlet.sample_rate*max_sec))

    ## get electrode index
    from get_channel_names import get_channel_names
    ROI_elec_names = ('F4',)
    channel_names = get_channel_names(inlet.info())
    ROI_elec_indexes = [index for index, name in enumerate(channel_names) if name in ROI_elec_names]
    assert len(ROI_elec_names) == len(ROI_elec_indexes), "names:{}, indexes:{}".format(ROI_elec_names,ROI_elec_indexes)

    # for display
    ## set stop key
    import sys
    esckey = 'escape'
    event.globalKeys.add(key=esckey, func=sys.exit)

    ## init psychopy
    win = circular_feedback(128, 'limegreen', size=[1920, 1080], units='pix', fullscr=True, allowGUI=False)

    ## set max experiment time
    routine_time = int(sys.argv[1])
    routine_timer = core.CountdownTimer(routine_time)

    while numpy.any(numpy.isnan(inlet.update()[0])):# check data
#        print(inlet.data)
        pass

    while routine_timer.getTime() > 0:
        # get EEG data
        data, timestamps = inlet.update()
        assert not numpy.any(numpy.isnan(data)), "data has 'nan' value :{}".format(data)

        if len(timestamps) == 0:
            continue
        eeg_buffer.extend(data[:, [ROI_elec_indexes]])

        if len(eeg_buffer) != eeg_buffer.maxlen:
            continue
        # fft
        psds, freq = wave2psd(eeg_buffer, inlet.sample_rate)
        amps = psds**0.5

        # display
        band = (8, 12) # alpha band
        r = amps[(band[0] < freq) & (freq < band[1])].mean() * 0.1
        win.circle.setRadius(r)
#        win.circle.setOpacity(0.5)
        win.circle.draw()
        win.flip()