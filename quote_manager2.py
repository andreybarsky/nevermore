# quote manager 2 handles csvs instead of xml

from xml.etree.ElementTree import Element, SubElement, tostring, parse
import csv
import os
import random
import datetime as dt
import platform

def timestamp():
    now = dt.datetime.now()
    stamp = (now.strftime('%d/%m/%y %H:%M'))
    return stamp

class QuoteBank(object):
    def __init__(self, server, load_existing=True):
        """A whole quote bank. Contains users, users contain quotes."""
        self.server = server
        self.users = {} # an empty dict that will contain usernames and quote lists

        self.numquotes = 0

        if platform.system()=='Windows':
            qdir = 'quotes\\'
        else:
            qdir = 'quotes/'

        self.filenamexml = qdir + server + '.xml'
        self.filenamecsv = qdir + server + '.csv'

        if load_existing:
            if os.path.isfile(self.filenamecsv):
                print('Importing csv...')
                self.from_csv(self.filenamecsv)
                print('Import successful.')
            else:
                if os.path.isfile(self.filenamexml):
                    print('Importing xml...')
                    self.from_xml(self.filenamexml)
                    print('Exporting to csv...')
                    self.to_csv()

                else: # create it
                    print('Creating csv...')
                    self.to_csv()

    def add(self, username, text, time=None):
        lusername = username.lower() # to keep this case insensitive
        if time is None:
            time = timestamp()
        if lusername not in self.users:
            self.users[lusername] = [] # an empty list that will contain Quotes

        quote = Quote(text, time, self.numquotes+1)
        try:
            self.users[lusername].append(quote)
            self.numquotes += 1
            with open(self.filenamecsv, 'a') as file:
                text = text.replace('"', "'") # replace double with single quotes
                ntext = '"' + text.replace('\n', '&&NEWLINE') + '"'
                lusername = '"' + lusername + '"'
                row = ','.join([self.server, lusername, ntext, time, str(self.numquotes)]) + '\n'
                file.write(row)
                print('quote added: %s' % text)
        except Exception as error:
            print('that failed somehow: %s' % error)

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

        out = "[{i}/{n}] ({t})\n<{u}> {q}"
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
                    out = "[{i}/{n}] ({t})\n<{u}> {q}"
                    return out.format(u=user, t=q.time, i=place, n=self.numquotes, q=q.text)

    def from_xml(self, filename=None):
        if filename is None:
            filename = self.filenamexml
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

    def to_csv(self):
        with open(self.filenamecsv, 'a') as file:
            i = 1
            for user in self.users:
                for quote in self.users[user]:
                    qtext = '"' + quote.text.replace('\n', '&&NEWLINE') + '"'
                    user = '"' + user + '"'
                    channel, username, text, tstamp, num = self.server, user, qtext, quote.time, str(i)
                    row = ','.join([channel, username, text, tstamp, num]) + '\n'
                    try:
                        file.write(row)
                        i += 1
                    except Exception as error:
                        print(error)
                        print(row)


    def from_csv(self, filename):
        with open(filename, 'r') as file:
            i = 1
            reader = csv.reader(file, quotechar='"', delimiter=",")
            for row in reader:
                channel, user, text, stamp, num = row
                text = text.replace('&&NEWLINE', '\n')
                if user in self.users:
                    self.users[user].append(Quote(text, stamp, int(num)))
                else:
                    self.users[user] = [Quote(text, stamp, int(num))]
                i += 1

        try:
            self.numquotes = int(num)
        except:
            self.numquotes = 0

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
    qb = QuoteBank('lf')

    #qb.from_xml()
    #.to_csv()