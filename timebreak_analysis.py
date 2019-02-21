from inlet_deque import InletDeque

if __name__ == '__main__':
    #histogram.py — Bokeh 1.0.4 documentation
    #https://bokeh.pydata.org/en/latest/docs/gallery/histogram.html

    import pylsl
    import sys
    import numpy
    import collections

    from bokeh.plotting import figure, show, output_file

    stream = pylsl.resolve_byprop(sys.argv[1], sys.argv[2])[0]
    inlet = InletDeque(
        stream, int(sys.argv[3]),
        processing_flags=pylsl.proc_clocksync | pylsl.proc_dejitter | pylsl.proc_monotonize
    )

    diff_timestamps = collections.deque()
    for i in range(int(sys.argv[4])):
        _, timestamps = inlet.update(allowed_timebreak=10.)
        diff_timestamps.extend((timestamps[1:] - timestamps[:-1])*1e3)#[s] -> [ms]
        hist, edges = numpy.histogram(diff_timestamps, density=True, bins=30)

        fig = figure(title='N = {}, samplint_rate = {}[Hz]'.format(len(diff_timestamps), int(inlet.samplint_rate)))
        fig.quad(top=hist, bottom=0, left=edges[:-1], right=edges[1:], fill_color='navy', line_color='white', alpha=0.5)
        fig.xaxis.axis_label = 'diff time[ms]'
        fig.yaxis.axis_label = 'times'
        show(fig)
