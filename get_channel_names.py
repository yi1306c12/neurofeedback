from pylsl import StreamInlet
from xml.etree import ElementTree

def get_channel_names(stream_info):
    info_xml = stream_info.as_xml()

    # parse info_xml
    root = ElementTree.fromstring(info_xml)

    return #list

if __name__ == '__main__':
    import sys
    prop, value = sys.argv[1], sys.argv[2]# in Quick-20, take "type" & "EEG"
    from pylsl import resolve_byprop
    streams = resolve_byprop(prop, value)

    channels = get_channel_names(stream[0].info())
    print(channels)
