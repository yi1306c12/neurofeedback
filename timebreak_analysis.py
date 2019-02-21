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

    _, timestamps = inlet.update(allowed_timebreak=10.)
    diff_timestamps = timestamps[1:] - timestamps[:-1]
    hist, edges = numpy.histogram(
        diff_timestamps*1e3,#[s] -> [ms]
        density=True, bins=50
        )

    fig = figure(
        title='N = {}, sampling_rate = {}[Hz], min,max = {:.4f}[ms],{:.4f}[ms]'.format(
            len(diff_timestamps),
            int(inlet.sampling_rate),
            min(diff_timestamps),
            max(diff_timestamps)
            ),
        y_range=(0,1)
        )#, y_axis_type='log')
    fig.quad(top=hist, bottom=0, left=edges[:-1], right=edges[1:], fill_color='navy', line_color='white', alpha=0.5)
    fig.xaxis.axis_label = 'diff time[ms]'
    fig.yaxis.axis_label = 'times'
    show(fig)
