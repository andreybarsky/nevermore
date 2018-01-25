from xml.etree.ElementTree import Element, SubElement, tostring, parse
from xml.dom import minidom
import os
import platform

def prettify(elem):
    """Return a pretty-printed XML string for the Element."""
    rough_string = tostring(elem, 'utf-8')
    reparsed = minidom.parseString(rough_string)
    return reparsed.toprettyxml(indent="  ")

class TagBank(object):
    def __init__(self, server):
        """A whole tag bank. Contains users, users contain tags."""
        self.server = server
        self.users = {} # an empty dict that will contain usernames and tags

        # if an xml file for this server exists: import it
        if platform.system()=='Windows':
            tdir = 'tags\\'
        else:
            tdir = 'tags/'

        self.filename = tdir + server + '.xml'

        if os.path.isfile(self.filename):
            print('Importing xml...')
            self.from_xml(self.filename)

        # else: # create it
        #     print('Creating xml...')
        #     self.to_xml()


    def addtag(self, username, tag):
        lusername = username.lower() # to keep this case insensitive
        if lusername not in self.users:
            self.users[lusername] = set() # an empty set that will contain tags

        if tag not in self.users[lusername]:
            self.users[lusername].add(tag)
        else:
            return ('%s is already %s' % (username, tag)) # only returns on failure

    def gettags(self, username):
        lusername = username.lower()
        if lusername not in self.users:
            return "No tags."
        else:
            tags = ', '.join(self.users[lusername])
            return tags

    def gettagged(self, tag):
        # search for inverse tags:
        ltag = tag.lower()
        tagged = []

        for username in self.users:
            these_tags = [x.lower() for x in self.users[username]]
            if ltag in these_tags:
                tagged.append(username)

        if len(tagged) == 0:
            return 'nobody.'
        return ', '.join(tagged)

    def to_xml(self):
        """Dumps the quote bank to an xml tree"""
        top = Element('%s_tagbank' % self.server)
        for user in self.users:
            u = SubElement(top, 'user', name=user)
            for tag in self.users[user]:
                t = SubElement(u, 'tag')
                t.text = tag

        with open(self.filename, 'w') as file:
            file.write(prettify(top))

    def from_xml(self, filename):
        """Imports xml tree from file"""

        tree = parse(filename)
        root = tree.getroot() # tagbank

        for u in root:
            user = u.attrib['name']
            self.users[user] = set()
            for t in u:
                tag = t.text
                self.users[user].add(tag)


if __name__=='__main__':
    tb = TagBank('bot_testing_server')

    tb.addtag('andrey', 'hitler')
    tb.addtag('andrey', 'stalin')
    tb.gettags('andrey')

    tb.to_xml()