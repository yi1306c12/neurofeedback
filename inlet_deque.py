# -*- coding: utf-8 -*-
"""
Example:
    print EEG data in a 3 seconds from labstreaminglayer as .csv format.
        $ python inlet_deque.py "type" "EEG" 3
"""
import collections
import numpy
import pylsl

from get_channel_names import get_channel_names

class TimeBreakError(RuntimeError):
    """
    This error will rise if InletDeque has detected a short break in _time_deque.
    """


class InletDeque:
    """
    What does the __init__ method do?
    Args:
        stream (pylsl.StreamInfo) :
        max_sec (int) :
    """

    def __init__(self, stream_info, max_sec, **inlet_keyargs):
        assert isinstance(max_sec, int), "The 'max_sec' should be integer."

        self.inlet = pylsl.StreamInlet(
            stream_info, max_sec, **inlet_keyargs
        )
        self.sampling_rate = self.inlet.info().nominal_srate()#stream_info.nominal_srate()
        maxlen = int(max_sec * self.sampling_rate)
        self._data_deque = collections.deque(maxlen=maxlen)
        self._time_deque = collections.deque(maxlen=maxlen)

    def clear_deques(self):
        """
        To avoid raising TimeBreakError in update.
        Calling this just before calling update() causes a block in update() during max_sec seconds.
        """
        self._data_deque.clear()
        self._time_deque.clear()

    def update(self, allowed_timebreak=None):
        """
        returns the last max_sec*nominal_samplingrate of streaming data as numpy.ndarray.
        The reasons changing returns into numpy.ndarray are
            1. for multiplicity of use (deque < numpy.ndarray) and
            2. to get copies to avoid users affect deques.

        Returns:
            numpy.array(self._data_deque) : The shape must be (maxlen, channels)
            numpy.array(self._time_deque) : The shape must be (maxlen,)

        ToDo:
            Detect a short break and raise an error.
        """
        while self.inlet.samples_available() or len(self._data_deque) != self._data_deque.maxlen:
            datas, timestamps = self.inlet.pull_chunk()
            self._data_deque.extend(datas)
            self._time_deque.extend(timestamps)

        if not allowed_timebreak is None:
            max_timebreak = max([t2 - t1 for t1, t2 in zip(self._time_deque, list(self._time_deque)[1:])])
            if max_timebreak > allowed_timebreak / self.sampling_rate:
                raise TimeBreakError("A short(={}) break detected in ".format(max_timebreak))

        return numpy.array(self._data_deque), numpy.array(self._time_deque)


if __name__ == '__main__':
    import sys
    stream = pylsl.resolve_byprop(sys.argv[1], sys.argv[2])[0]
    inlet_deque = InletDeque(
        stream,
        int(sys.argv[3]),
        processing_flags=pylsl.proc_clocksync | pylsl.proc_dejitter | pylsl.proc_monotonize
    )

    try:
        sequence_of_data, sequence_of_timestamps = inlet_deque.update()#allowed_timebreak=5.)
    except TimeBreakError:
        #This block must not be used.
        inlet_deque.clear_deques()
        raise

    from get_channel_names import get_channel_names
    print('timestamp', *get_channel_names(inlet_deque.inlet.info()), sep=',')
    for timestamp, data in zip(sequence_of_timestamps, sequence_of_data):
        print(timestamp, *data, sep=',')
