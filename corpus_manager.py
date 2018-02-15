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

    splitted = re.findall(r"[\S']+|[.,!?;]", corpus)

    server_chain = build_chain(splitted)
    server_chain2 = build_chain2(splitted)
    return server_chain, server_chain2

def build_chain(words):
    chain = {}
    print('length of starting chain: %s' % len(chain))
    index = 1
    for word in words[index:]:
        key = words[index - 1]
        if key[:2] != '<@': # filter out mentions
            if key in chain:
                chain[key].append(word)
            else:
                chain[key] = [word]
        index += 1
    return chain

def build_chain2(words):
    # second order markov chain
    chain2 = {}
    index = 2
    for word in words[index:]:
        dkey = (words[index-2], words[index-1])
        if dkey in chain2:
            chain2[dkey].append(word)
        else:
            chain2[dkey] = [word]
        index += 1
    return chain2


def generate_message(chain, seed=['END'], count=100, verbose_failure=True):
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
                if verbose_failure:
                    return "%s? that doesn't make any sense" % word1
                else:
                    return None

        attempts += 1

        finalmessage = message.replace('END', '')

    if attempts == 50:
        if verbose_failure:
            return "that doesn't make any sense at all."
        else:
            return None
    else:
        print('Made a markov chain: %s' % finalmessage)
        return finalmessage

def generate_message2(chain1, chain2, seed=['END'], min=25, max=200, max_attempts=50, verbose_failure=True):
    """Generates a 2nd order markov chain"""
    print('Making 2nd order markov chain...')
    if verbose_failure:
        failure = random.choice(["that doesn't make any sense.",
        "wtf",
        "what",
        "no.",
        "I can't do that.",
        "doesn't look like anything to me."])
    else:
        failure = None
    # process the seed or pick a random one:
    if len(seed) >= 2: # we need at least two words usually
        seedl = [x.lower() for x in seed]
        message = ' '.join(seedl)
        wordkey = tuple(seedl[-2:])
        if wordkey not in chain2: # if we haven't seen this sequence
            if wordkey[1] not in chain1: # if we've never seen this word:
                print('never seen the word %s' % wordkey[1])
                return failure
            else:
                new_word = random.choice(chain1[wordkey[1]])
                wordkey = (wordkey[1], new_word)
                if new_word in ['.',',', '!', '?', ';']: # deal with punctuation appropriately
                    message += new_word
                else:
                    message += ' ' + new_word
    elif len(seed) == 1: # single word seed
        word1 = seed[0]
        if word1 == 'END': # if blank seed just pick from our chain2:
            wordkey = random.choice(list(chain2.keys()))
            if wordkey[0] in ['.',',', '!', '?', ';']: # deal with punctuation appropriately
                message = ''.join(wordkey)
            else:
                message = ' '.join(wordkey)
        else: # try and start a new sentence with that word
            wordkey = ('END', word1)
            if wordkey in chain2: # new sentence
                message = word1 # but don't include END
            elif word1 in chain1: # have we ever seen this word before
                word2 = random.choice(chain1[word1]) # pick a random next word from 1st-order chain
                wordkey = (word1, word2)
                message = ' '.join(wordkey)
            else: # totally new word
                print('never seen the word %s '% word1)
                return failure
    assert wordkey in chain2 # wordkey should be valid for chain2 now
    print('%s exists in chain2' % str(wordkey))
    # move on to generating rest of chain
    attempt = 0
    finalmessage = ''
    valid = False
    while not valid:
        next_word = None
        while next_word != 'END':
            # print("pulling a random continuation from chain2 for %s" % str(wordkey))
            next_word = random.choice(chain2[wordkey])
            if next_word in ['.',',', '!', '?', ';']: # deal with punctuation appropriately
                message += next_word
            else:
                message += ' ' + next_word
            wordkey = (wordkey[1], next_word)
        finalmessage = message.replace('END', '')
        finalmessage = finalmessage.replace('  ', ' ')

        if attempt > max_attempts:
            return failure
        elif len(finalmessage) < min or len(finalmessage) > max:
            attempt += 1
        else:
            valid = True
    print('Made a markov chain:\n%s' % finalmessage)
    return finalmessage