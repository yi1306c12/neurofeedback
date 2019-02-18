from pylsl import StreamInlet
from xml.etree import ElementTree

def get_channel_names(stream_info):
    info_xml = stream_info.as_xml()

    # parse info_xml
    root = ElementTree.fromstring(info_xml)

    return [label.text for label in root.findall('.//label')]

if __name__ == '__main__':
    import sys
    prop, value = sys.argv[1], sys.argv[2]# in Quick-20, take "type" & "EEG"
    from pylsl import resolve_byprop
    streams = resolve_byprop(prop, value)

    stream_info = StreamInlet(streams[0]).info()
    channels = get_channel_names(stream_info)
    print(channels)
