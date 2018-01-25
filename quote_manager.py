from xml.etree.ElementTree import Element, SubElement, tostring, parse
from xml.dom import minidom
import os
import random
import datetime as dt
import platform

def prettify(elem):
    """Return a pretty-printed XML string for the Element."""
    rough_string = tostring(elem, 'utf-8')
    reparsed = minidom.parseString(rough_string)
    return reparsed.toprettyxml(indent="  ")

def timestamp():
    now = dt.datetime.now()
    stamp = (now.strftime('%d/%m/%y %H:%M'))
    return stamp

class QuoteBank(object):
    def __init__(self, server):
        """A whole quote bank. Contains users, users contain quotes."""
        self.server = server
        self.users = {} # an empty dict that will contain usernames and quote lists

        self.numquotes = 0

        if platform.system()=='Windows':
            qdir = 'quotes\\'
        else:
            qdir = 'quotes/'
        self.filename = qdir + server + '.xml'


        if os.path.isfile(self.filename):
            print('Importing xml...')
            self.from_xml(self.filename)
            #self.numquotes = self.count_quotes()

        #else: # create it
        #    print('Creating xml...')
        #    self.to_xml()

    def add(self, username, text):
        lusername = username.lower() # to keep this case insensitive
        time = timestamp()
        if lusername not in self.users:
            self.users[lusername] = [] # an empty list that will contain Quotes

        quote = Quote(text, time, self.numquotes+1)
        self.users[lusername].append(quote)
        self.numquotes += 1

    def get(self, username, *args):
        """Gets quotes from a username, with optional 1-indexed int parameter"""
        lusername = username.lower()
        if lusername not in self.users:
            return "No quotes found for that user."

        nquotes = len(self.users[lusername])
        if nquotes == 0:
            return "No quotes found for that user."

        if not args: # no positional argument, so choose a random quote
            idx = random.randint(0, nquotes-1)
            q = self.users[lusername][idx]
            idx += 1 # count from 1
        else:
            idx = args[0] # index specified by user, assume between 1:nquotes inclusive
            if idx > 0:
                q = self.users[lusername][idx-1] # switch to python style indexing
            elif idx < 0:
                q = self.users[lusername][idx]
                idx = (nquotes)+idx+1 # for formatting, we dont want to show -1

        out = "[{i}/{n}] ({t})\n{u}: {q}"
        return out.format(u=username, t=q.time, i=idx, n=nquotes, q =q.text)

    def allquote(self, *place_arg):
        """Regardless of user information, retrieves a quote from all stored quotes"""
        if not place_arg:
            place = random.randint(1,self.numquotes)
        else:
            place = place_arg[0] # extract from tuple
            if place < 0:
                place = self.numquotes + 1 + place
        allusers = [u for u in self.users]
        allquotes = []
        for user in allusers:
            quotes = self.users[user]
            for q in quotes:
                if q.number == place:
                    out = "[{i}/{n}] ({t})\n{u}: {q}"
                    return out.format(u=user, t=q.time, i=place, n=self.numquotes, q=q.text)

    def to_xml(self):
        """Dumps the quote bank to an xml tree"""
        top = Element('%s_quotebank' % self.server, numquotes=str(self.numquotes))
        for user in self.users:
            u = SubElement(top, 'user', name=user)
            for quote in self.users[user]:
                q = SubElement(u, 'quote', time=quote.time, number=str(quote.number))
                q.text = quote.text

        with open(self.filename, 'w') as file:
            file.write(prettify(top))

    def from_xml(self, filename):
        tree = parse(filename)
        root = tree.getroot()  # quotebank
        self.numquotes = int(root.attrib['numquotes'])
        for u in root:
            user = u.attrib['name']
            self.users[user] = []
            for q in u:
                time = q.attrib['time']
                number = int(q.attrib['number'])
                text = q.text
                thisquote = Quote(text, time, number)
                self.users[user].append(thisquote)

    def count_quotes(self):
        q = 0
        allusers = [u for u in self.users]
        for user in allusers:
            for quotes in user:
                q += 1

    def number_quotes(self):
        """assigns numbers to quotes that dont have them"""
        pass

class Quote(object):
    def __init__(self, text, time, number):
        self.text = text
        self.time = time
        self.number = number

if __name__=='__main__':
    qb = QuoteBank('__.')

    qb.to_xml()