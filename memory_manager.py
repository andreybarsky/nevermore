from xml.etree.ElementTree import Element, SubElement, tostring, parse
from xml.dom import minidom
from quote_utils import to_filename
import os, platform

def prettify(elem):
    """Return a pretty-printed XML string for the Element."""
    rough_string = tostring(elem, 'utf-8')
    reparsed = minidom.parseString(rough_string)
    return reparsed.toprettyxml(indent="  ")

class MemBank(object):
    def __init__(self, server):
        "Contains stored commands from users"
        self.server = server
        self.memories = {}

        if platform.system()=='Windows':
            mdir = 'cmds\\'
        else:
            mdir = 'cmds/'
        self.filename = mdir + to_filename(self.server) + '.xml'

        if os.path.isfile(self.filename):
            print('Importing cmds xml...')
            self.from_xml(self.filename)

    def remember(self, key, val):
        msg = None
        if key in list(self.memories.keys()):
            msg = f'Forgetting {key}: {self.memories[key]}\n'
        self.memories[key] = val
        self.to_xml()
        # msg += f'Remembering {key}'
        return msg

    def recall(self, key):
        return self.memories[key]

    def forget(self, key):
        msg = f'Forgetting {key}: {self.memories[key]}'
        del self.memories[key]
        self.to_xml()
        return msg

    def to_xml(self):
        """Dumps the commands to an xml tree"""
        top = Element('%s_membank' % self.server)
        for key in self.memories.keys():
            u = SubElement(top, 'cmd', name=key)
            u.text = self.memories[key]

        with open(self.filename, 'w') as file:
            file.write(prettify(top))

    def from_xml(self, filename):
        tree = parse(filename)
        root = tree.getroot()  # memquotebank
        for u in root:
            key = u.attrib['name']
            self.memories[key] = u.text
