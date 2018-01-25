from quote_utils import to_filename
import platform
import re
import random

if platform.system() == 'Windows':
    cdir = 'corpora\\'
else:
    cdir = 'corpora/'

def write(msg, server):
    filename = cdir + to_filename(server) + '_corpus.txt'
    with open(filename, 'a') as f:
        f.write(msg + '\n')

def server_chain(server): # create transitional probability matrix for server log
    filename = cdir + to_filename(server) + '_corpus.txt'
    with open(filename, encoding='latin-1') as f:
        corpus = f.read().lower()

    #remove uninteresting lines:
    lines = corpus.split('\n')

    newlines = []
    for x in lines:
        if x != '' and x[0] != '!' and x[0] != '.':
            newlines.append(x)

    corpus = ' END '.join(newlines)

    splitted = re.findall(r"[\w']+|[.,!?;]", corpus)

    server_chain = build_chain(splitted)
    return server_chain

def build_chain(words, chain={}):
    index = 1
    for word in words[index:]:
        key = words[index - 1]
        if key in chain:
            chain[key].append(word)
        else:
            chain[key] = [word]
        index += 1

    return chain

def generate_message(chain, seed=['END'], count=100):
    """Seed is the starting point for the chain - must be a list!!!"""
    print('Making markov chain...')
    finalmessage = ""
    attempts = 0
    while len(finalmessage) < 20 and attempts < 50:
        if len(seed) > 1:
            seedl = [x.lower() for x in seed]
            message = ' '.join(seedl)
            word1 = seedl[-1]
        else:
            word1 = seed[0]
            if word1 != 'END':
                word1 = word1.lower()
            message = word1

        ended = False
        while len(message.split(' ')) < count and not ended:
            if word1 in chain:
                word2 = random.choice(chain[word1])
                word1 = word2
                if word1 != 'END':
                    if word1 in ['.',',', '!', '?', ';']:
                        message += word2
                    else:
                        message += ' ' + word2
                    count += 1
                else:
                    ended = True
            else:
                return "%s? that doesn't make any sense" % word1

        attempts += 1

        finalmessage = message.replace('END', '')

    if attempts == 50:
        return "that doesn't make any sense at all."
    else:
        print('Made a markov chain: %s' % finalmessage)
        return finalmessage