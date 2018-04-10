# updated

import discord, asyncio
from discord.ext import commands
import logging
import time
import random
import os
import math

import quote_manager2 as qm
import tag_manager as tm
import corpus_manager as cm
import memory_manager as mm

from quote_utils import qparse, to_filename, is_number

with open('token.txt', 'r') as file:
    token = file.read()[:-1]
description = "i'm a markov bot. type .help for help"

bot = commands.Bot(command_prefix='.', description=description)
bot.remove_command('help')

# features to be added:
# handle multi line quotes from compact mode

tags = tm.TagBank('discord')
last_reply = 0


def get_name(author, serv=None):
    """Gets the name or nick of an Author object
    or randomly uses one of their tags if serv isn't None
    assumes serv is a cleaned up string that can be passed to tagbank"""
    name = author.nick
    if name is None:
        name = str(author).split('#')[0]

    if serv is not None: # if serv is None, we just get their actual name, else we pick a fun tag from that server's tagbank:
        tags = tm.TagBank(serv) # get tags
        tagstring = tags.gettags(name.lower())
        if tagstring == 'No tags.':
            return name
        else:
            taglist = tagstring.split(', ')
            possible_names = taglist + [name] # list of real name and tags
            newname = random.choice(possible_names) # choose one randomly
            return newname
    else:
        return name

@bot.event
async def on_ready():
    print('Logged in as')
    print(bot.user.name)
    print(bot.user.id)
    print('------')

    bot.last_reply = 0
    bot.shames = ["that's weak.",
                    "pathetic.",
                    "you think that's funny?",
                    "get a grip.",
                    "can you believe this guy?",
                    "haha, no",
                    "no.",
                    "get over yourself."]

    bot.markovchains = {} # dict keys are servers
    bot.markovchains2 = {} # second order dependencies

    bot.cmds = {} # dict keys are servers
    bot.corpus_last_read = 0

    bot.beaten_to_the_punch = False

    print([str(x) for x in bot.servers])




@bot.command(pass_context=True)
async def q(ctx, arg1 : str = 'all', *words : str):
    """add <name> <quote>: Adds a quote to someone.
    <name> [<idx>]: Retrieves a quote from someone, optionally indexed by quote number."""
    serv = to_filename(str(ctx.message.server))

    print('server name: %s' % serv)
    quotes = qm.QuoteBank(serv)

    if arg1 == 'add':
        # add a quote
        user = words[0]

        if '|' in words: # detect multi-word usernames
            user, restwords = (' '.join(words)).split(' | ')

            fullmsg = ctx.message.content  # have to parse the full message to preserve newlines
            msg = fullmsg.split('| ')[1]  # separate out the |
        elif len(ctx.message.mentions) > 0:
            print('mention detected')
            mention = ctx.message.mentions[0]
            user = get_name(ctx.message.mentions[0])
            fullmsg = ctx.message.content
            print('fullmsg: %s' % fullmsg)
            id = "<@%s>" % ctx.message.mentions[0].id
            msg = fullmsg.split('.q add ' + id + ' ')[1]
            print('msg: %s' % msg)

        else:
            fullmsg = ctx.message.content # have to parse the full message to preserve newlines
            msg = fullmsg.split('.q add ' + user + ' ')[1] # separate out the .q add

        quote = qparse(msg, user)

        print('Adding quote:\n%s::%s' % (user, quote))

        # check for self quoting:
        if user.lower() == get_name(ctx.message.author, serv=None).lower():
            msg = random.choice(bot.shames)
            tags = tm.TagBank(serv)
            ret = tags.addtag(user, 'self quoter')
            tags.to_xml()

            await bot.say(msg)

        else:
            quotes.add(user, quote)
            #quotes.to_xml()
            await bot.say('Quote added.')


    else:
        # say a quote
        if arg1 == 'all': # grab a quote irrespective of user
            q = quotes.allquote()
        elif is_number(arg1):
            # get an allquote with index
            q = quotes.allquote(int(arg1))

        else: # grab a random quote from the named user
            user = arg1
            if '|' in words: # detect multi line usernames
                user, words = (' '.join(words)).split(' | ')
            elif len(ctx.message.mentions) > 0: # detect mentions
                print('mention detected')
                mention = ctx.message.mentions[0]
                user = get_name(ctx.message.mentions[0]) # keep words the same; the mention is arg1

            if len(words) > 0: # we've been asked for an index, or a multi line username, or both
                if is_number(words[-1]): # there is an index
                    idx = int(words[-1]) # retrieve index

                    words = words[:-1]
                    if len(words) > 0: # are we dealing with a multi word username?
                        user = "%s %s" % (user, ' '.join(words)) # complete the username
                    q = quotes.get(user, idx) # multi word username with index
                else: # no index, just a multi word username on its own
                    user = "%s %s" % (user, ' '.join(words))
                    q = quotes.get(user) # multi word username without index

            else: # get a random quote
                q = quotes.get(user)

        await bot.say(q)

@bot.command(pass_context=True)
async def lf(ctx, user : str = 'all', *args : str):
    """Just like getting quotes, but from lf"""
    serv = 'lf'
    print('getting quotes, server name: %s' % serv)
    quotes = qm.QuoteBank(serv)

    q = None
    print('user: %s' % user)
    if user == 'all':  # grab a quote irrespective of user
        print('calling allquote()')
        attempt = 1
        while q is None and attempt < 20: # some quotes are empty?
            q = quotes.allquote()
            attempt += 1
    elif is_number(user):
        # get an allquote with index
        print('calling allquote(int(user))')
        q = quotes.allquote(int(user))

    else:  # grab a random quote from the named user
        if '|' in args:  # detect multi line usernames
            user, args = (' '.join(words)).split(' | ')
        elif len(ctx.message.mentions) > 0:  # detect mentions
            print('mention detected')
            mention = ctx.message.mentions[0]
            user = get_name(ctx.message.mentions[0])  # keep words the same; the mention is arg1

        if len(args) > 0:  # we've been asked for an index, or a multi line username, or both
            if is_number(args[-1]):  # there is an index
                idx = int(args[-1])  # retrieve index

                args = args[:-1]
                if len(args) > 0:  # are we dealing with a multi word username?
                    user = "%s %s" % (user, ' '.join(args))  # complete the username
                q = quotes.get(user, idx)  # multi word username with index
            else:  # no index, just a multi word username on its own
                user = "%s %s" % (user, ' '.join(args))
                q = quotes.get(user)  # multi word username without index

        else:  # get a random quote
            attempt = 1
            while q is None and attempt < 20:
                q = quotes.get(user)
                attempt += 1

    print('Got a quote: %s' % q)
    await bot.say(q)

@bot.command(pass_context=True, aliases=['name', 'god'])
async def pretender(ctx):
    serv = 'lf'
    print('getting quotes, server name: %s' % serv)
    qb = qm.QuoteBank(serv)

    attempt = 1
    valid = False

    while not valid and attempt < 500:
        random_quote = qb.get('kevin').split('<kevin>')[1]
        if len(random_quote) <= 33 and random_quote[:4] != 'http':
            valid = True
        else:
            attempt += 1
    if valid:
        await bot.say(random_quote)
    else:
        await bot.say('Pro-transmasculine enslavement.')

@bot.command(pass_context=True)
async def tag(ctx, user : str, *tag : str):
    """<name> <tag>: Tag someone as something."""

    print('user: %s' % user)
    print('tag: %s' % str(tag))

    # detect multi word usernames:
    if '|' in tag:
        user2, tag = (' '.join(tag)).split(' | ')
        print("user2: %s\ntag: %s" % (user2, tag))
        user = user + ' ' + user2
    elif len(ctx.message.mentions) > 0:
        print('mention detected')
        mention = ctx.message.mentions[0]
        user = get_name(ctx.message.mentions[0])
        tag = ' '.join(tag)  # extract string from 1-tuple
    else:
        tag = ' '.join(tag) # extract string from 1-tuple
    serv = to_filename(str(ctx.message.server))

    print('server name: %s' % serv)
    tags = tm.TagBank(serv)

    # check for self taggers:
    if user.lower() == get_name(ctx.message.author, serv=None).lower():
        msg = random.choice(bot.shames)
        tags = tm.TagBank(serv)
        ret = tags.addtag(user, 'self tagger')
        tags.to_xml()

        await bot.say(msg)

    else:
        ret = tags.addtag(user, tag)
        tags.to_xml()

        if ret is not None: # tagbank tells us there are no tags
            await bot.say(ret)
        else:
            tagstring = tags.gettags(user)
            await bot.say("%s: %s" % (user, tagstring))

@bot.command(pass_context=True)
async def tags(ctx, *user : str):
    """<name>: Show someone's tags."""
    serv = to_filename(str(ctx.message.server))
    user = ' '.join(user)
    print('user parsed as: %s' % user)

    if len(ctx.message.mentions) > 0:
        print('mention detected')
        mention = ctx.message.mentions[0]
        name = get_name(ctx.message.mentions[0])
        print('name parsed as: %s' % name)
    else:
        name = user
        print('name parsed as: %s' % name)

    tags = tm.TagBank(serv)
    tagstring = tags.gettags(name)
    await bot.say("%s: %s" % (name, tagstring))

@bot.command(pass_context=True, name='is')
async def is_tag(ctx, user : str, *tag_question : str):
    """<name> <tag>: Is this person something?."""
    serv = to_filename(str(ctx.message.server))
    #user = ' '.join(user)
    print('user parsed as: %s' % user)

    if len(ctx.message.mentions) > 0:
        print('mention detected')
        mention = ctx.message.mentions[0]
        name = get_name(ctx.message.mentions[0])
        print('name parsed as: %s' % name)
    else:
        name = user
        print('name parsed as: %s' % name)

    tag_question = ' '.join(tag_question)

    tags = tm.TagBank(serv)
    tagstring = tags.gettags(name)
    taglist = tagstring.split(', ')
    if tag_question in taglist:
        msg = 'yes'
    else:
        msg = 'no'
    await bot.say(msg)


@bot.command(pass_context = True)
async def tagged(ctx, *tag : str):
    """<tag>: Show everyone who is tagged as this."""
    serv = to_filename(str(ctx.message.server))
    print(tag)
    tag = ' '.join(tag)
    tags = tm.TagBank(serv)
    userstring = tags.gettagged(tag)
    await bot.say("%s: %s" % (tag, userstring))

@bot.command(pass_context = True)
async def markov(ctx, *seed : str):
    serv = to_filename(str(ctx.message.server))
    print('server name: %s' % serv)

    if len(ctx.message.mentions) > 0:
        print('mention detected')
        mention = ctx.message.mentions[0]
        name = get_name(ctx.message.mentions[0])
        if len(seed) == 1:
            # we've been asked to make a markov from just a mention, so just convert it to string:
            seed = [name]

    # if we haven't loaded the chain for this server, or if we haven't loaded one in a while:
    if serv not in bot.markovchains or time.time() - bot.corpus_last_read > (60*60):
        print('Loading corpus from %s' % serv)
        bot.markovchains[serv], bot.markovchains2[serv] = cm.server_chain(serv)
        print('Chain1: %s units long' % len(bot.markovchains[serv]))
        print('Chain2: %s units long' % len(bot.markovchains2[serv]))
        bot.corpus_last_read = time.time()

    if seed == ():
        seed = ['END']
    else:
        seed = [x.lower() for x in seed] # lowercase the seed

    print('trying to make a markov chain...')
    msg = cm.generate_message2(bot.markovchains[serv], bot.markovchains2[serv], seed=seed)
    if msg is not None:
        await bot.say(msg)

@bot.command(pass_context = True, name='in')
async def markov_in(ctx):
    serv = to_filename(str(ctx.message.server))
    if serv not in bot.markovchains or time.time() - bot.corpus_last_read > (60*60):
        print('Loading corpus from %s' % serv)
        bot.markovchains[serv], bot.markovchains2[serv] = cm.server_chain(serv)
        print('Chain1: %s units long' % len(bot.markovchains[serv]))
        print('Chain2: %s units long' % len(bot.markovchains2[serv]))
        bot.corpus_last_read = time.time()
    seed = ['*in']
    print("trying to make a markov chain, but with 'in'")
    valid = False
    attempts = 0
    while not valid and attempts < 30:
        msg = cm.generate_message2(bot.markovchains[serv], bot.markovchains2[serv], seed=seed)
        if 'voice*' in msg:
            valid = True
        else:
            attempts += 1
    print('made a 2nd order markov chain with in:\n%s' % msg)
    if msg is not None:
        await bot.say(msg)

@bot.event
async def on_message(message):
    msg = None
    # we do not want the bot to reply to itself
    if message.author != bot.user:
        cmd = message.content.lower()
        serv = to_filename(str(message.server))

        if 'ty bot' in cmd or 'thanks bot' in cmd or 'thanks nevermore' in cmd or 'ty nevermore' in cmd or 'thx bot' in cmd or 'thx nevermore' in cmd:
            requester = get_name(message.author, to_filename(str(message.server)))
            responses = ["you're welcome, {}",
                        "ur welcome, {}",
                        "no problem, {}",
                        "any time, {}",
                        "my pleasure, {}"]
            msg = (random.choice(responses).format(requester))
        elif time.time() - bot.last_reply > 60: # 60 sec cooldown
            if 'bad bot' in cmd:
                msg = ':('
            elif 'good bot' in cmd:
                msg = ':)'
            elif cmd in ['hello bot', 'hi bot', 'hello nevermore', 'hi nevermore']:
                name = message.author.nick
                if name is None:
                    name = get_name(message.author, serv)
                greeting = random.choice(['hi', 'hello'])
                msg = '%s %s' % (greeting, name)
            elif 'how do' in cmd and 'feel' not in cmd and len(cmd) < 100: # we want "how do", but not "how do i/you feel"
                chance = 0.25
                roll = random.uniform(0, 1)
                if roll < chance:
                    time.sleep(3) # for comedic effect
                    msg = 'very carefully.'
            elif 'my wife' in cmd:
                msg = 'MY WIFE.'
            elif 'so bad' in cmd or 'very bad' in cmd or 'really bad' in cmd or 'insanely bad' in cmd or 'incredibly bad' in cmd or 'unbelievably bad' in cmd:
                print('I smell something bad.')
                print('the server is: %s' % serv)
                if serv == 'very_official_discord_server' or serv=='bot_testing_server': # this is a dom goons injoke
                    print("so I'm considering making the joke")
                    if 'very bad' in cmd or 'so bad' in cmd or 'really bad' in cmd:
                        chance = 0.25
                    else:
                        chance = 0.5
                    roll = random.uniform(0, 1)
                    print('The roll is: %s' % roll)
                    if roll < chance:
                        time.sleep(3) # for comedic effect
                        msg = 'much like your posting'
            elif 'anime' in cmd:
                chance = 0.3
                roll = random.uniform(0,1)
                if roll < chance:
                    msg = "I think you mean animé."
            elif len(message.mentions) > 0:
                print('mention detected')
                mention = message.mentions[0]
                name = get_name(message.mentions[0])
                if name == 'nevermore':
                    # someone is addressing us directly!
                    print("someone's talking about me")
                    # do something here

            else:
                # a random chance to spit out a markov chain
                chance = 0.02
                roll = random.uniform(0,1)
                print('Random markov roll: %.2f' % roll)
                if roll < chance and cmd[0] != '.': # don't do this for bot commands
                    # if we haven't loaded the chain for this server, or if we haven't loaded one in a while:
                    if serv not in bot.markovchains or time.time() - bot.corpus_last_read > (60*60):
                        print('Loading corpus from %s' % serv)
                        bot.markovchains[serv], bot.markovchains2[serv] = cm.server_chain(serv)
                        print('The result chain is %s units long' % len(bot.markovchains[serv]))
                        bot.corpus_last_read = time.time()
                    msg = cm.generate_message2(bot.markovchains[serv], bot.markovchains2[serv], seed=['END'])

        if msg is not None:
            bot.last_reply = time.time()
            await bot.send_message(message.channel, msg)

        # record raw messages to corpus:
        cm.write(cmd, serv)

    await bot.process_commands(message)

@bot.command(pass_context = True)
async def remember(ctx, *args):
    key = args[0].lower()
    print(f'Remembering {key}')
    tag = ctx.message.content.split('.remember ' + key + ' ')[1]

    if key[0] == '.': # in case someone types the dot for the tag
        key = tag[1:]
    serv = to_filename(str(ctx.message.server))
    if serv not in bot.cmds: # load the xml:
        bot.cmds[serv] = mm.MemBank(serv)

    # check if the new cmd isn't an existing command:
    if key in list(bot.commands.keys()):
        print('invalid, that command already exists!')
        return

    outcome = bot.cmds[serv].remember(key, tag)

    requester = get_name(ctx.message.author, to_filename(str(ctx.message.server)))

    acknowledgements = ["you got it, {}.",
                        "sure thing, {}.",
                        "ok, {}.",
                        "will do, {}.",
                        "I will, {}.",
                        "whatever you want, {}.",
                        "if you say so, {}."]

    msg = (random.choice(acknowledgements).format(requester))

    if outcome is not None:
        msg += '\n' + outcome # tell them what we forgot
    await bot.say(msg)


@bot.command(pass_context = True)
async def forget(ctx, key):
    key = key.lower()
    print(f'Forgetting {key}')
    serv = to_filename(str(ctx.message.server))
    if serv not in bot.cmds: # load the xml:
        bot.cmds[serv] = mm.MemBank(serv)

    msg = bot.cmds[serv].forget(key)
    await bot.say(msg)

@bot.command(pass_context = True, aliases=['DRN'])
async def drn(ctx):
    def d6():
        return random.randint(1,6)

    print('I heard:\n%s' % ctx.message.content)
    if ctx.message.content == '.drn':
        num_to_roll = 1
    else:
        num_to_roll = 2

    rolls = 0

    cumtotal = 0
    while rolls < num_to_roll:
        roll = d6()
        print('rolled %d' % roll)
        cumtotal += roll

        if roll == 6:
            num_to_roll += 1
            cumtotal -= 1
        rolls += 1

    msg = str(cumtotal)
    await bot.say(msg)

@bot.command(pass_context = True, aliases=['RIP'])
async def rip(ctx, *dead : str):

    inp = ' '.join(dead).upper()

    max_len = 40

    if len(inp) < 5:
        switch = 1
        while len(inp) < 5:
            if switch == 1:
                inp += ' '
                switch *= -1
            else:
                inp = ' ' + inp
                switch *= -1
        inplen = len(inp)
        stone_innerlen = inplen + 2
        stone_toplen = inplen - 2
        inputlist = [inp]
    elif len(inp) > max_len:
        inputlist = []
        while len(inp) > max_len:
            inputlist.append(inp[:max_len])
            inp = inp[max_len:]
        inputlist.append(inp + (' ' * (max_len - len(inp))))
        stone_innerlen = max_len + 2
        stone_toplen = max_len - 2
        inplen = max_len
    else:
        inplen = len(inp)
        stone_innerlen = inplen + 2
        stone_toplen = inplen - 2
        inputlist = [inp]

    topline = '**``` _.' + ('-' * stone_toplen) + '._ '
    lines = [topline]

    rip_space = (inplen-1) / 2
    rip_lspace = int(math.floor(rip_space))
    rip_rspace = int(math.ceil(rip_space))

    ripline = '|' + (' '*rip_lspace) + 'RIP' + (' ' * rip_rspace) + '|'

    lines.append(ripline)
    lines.append('|' + (' '*stone_innerlen) + '|')

    for inp in inputlist:
        lines.append('| ' + inp + ' |')

    lines.append('|' + (' '*stone_innerlen) + '|')
    lines.append('|' + ('_'*stone_innerlen) + '|```**')

    await bot.say('\n'.join(lines))

@bot.event
async def on_command_error(error, ctx):
    # this is a MASSIVE hack but it is how we allow users to set new commands dynamically
    if isinstance(error, commands.CommandNotFound):
        # recall from cmds:

        serv = to_filename(str(ctx.message.server))
        if serv not in bot.cmds:
            bot.cmds[serv] = mm.MemBank(serv)

        cmd = ctx.message.content[1:].lower()
        if cmd in bot.cmds[serv].memories:
            print('I remember this one:')
            print(bot.cmds[serv].recall(cmd))
            recall = bot.cmds[serv].recall(cmd)
            await bot.send_message(ctx.message.channel, f'{recall}')

        else:
            print('nobody has set that command!')
    else:
        print('===bot error:\n%s' % error)

@bot.command(pass_context = True, aliases=['list', 'what'])
async def womble(ctx):
    serv = to_filename(str(ctx.message.server))
    if serv not in bot.cmds:
        bot.cmds[serv] = mm.MemBank(serv)

    #print(bot.cmds[serv].memories)
    memories = [x for x in bot.cmds[serv].memories.keys()]
    msg = ', '.join(memories)
    await bot.say(msg)


@bot.command(pass_context = True)
async def help(ctx):
    print(ctx)
    helpstr = """Commands:
.q add <name> <quote>: Add a quote to someone.
    or: .q add <long name> | <quote>
.q <name> [<idx>]: Retrieves a quote from someone, either random or indexed by a number.
.q [<idx>]: Retrieve a quote from the whole server, either random or indexed by a number.

.tag <name> <tag>: Adds a tag to someone.
    or: .tag <long name> | <tag>
.tags <name>: Shows the tags for someone.
.tagged <tag>: Shows everyone with this tag.

.markov [<seed>]: Start a Markov chain, optionally seeded by some words.

.remember <cmd> <content>: Remembers a command to be used in the future.
.<cmd>: Recall the content of a command.
.list: Display the commands that are currently memorised for this server.

.request <feature>: Request a new feature.

"""
    await bot.say(helpstr)

@bot.command(pass_context = True)
async def request(ctx, *words):
    requester = get_name(ctx.message.author, to_filename(str(ctx.message.server)))
    real_name = get_name(ctx.message.author, None)
    filename = 'feature_requests.txt'
    msg = ctx.message.content
    with open(filename, 'a') as f:
        f.write("%s: %s\n" % (real_name, msg))

    acknowledgements = ["I'll keep that in mind, {}.",
                        "good idea, {}.",
                        "that's a terrible idea, {}.",
                        "I'll think about it, {}.",
                        "interesting thought, {}.",
                        "I like the sound of that, {}.",
                        "why would you want that, {}."]

    await bot.say(random.choice(acknowledgements).format(requester))

@bot.command(pass_context = True)
async def loadmarkov(ctx, servername):
    serv = to_filename(servername)
    print('Loading corpus from %s' % serv)
    bot.markovchains[serv], bot.markovchains2[serv] = cm.server_chain(serv)
    print('Chain1: %s units long' % len(bot.markovchains[serv]))
    print('Chain2: %s units long' % len(bot.markovchains2[serv]))
    bot.corpus_last_read = time.time()

@bot.command(pass_context = True)
async def servmarkov(ctx, servername):
    serv = to_filename(servername)
    seed = ['END']

    if serv not in bot.markovchains or time.time() - bot.corpus_last_read > (60*60):
        print('Loading corpus from %s' % serv)
        bot.markovchains[serv], bot.markovchains2[serv] = cm.server_chain(serv)
        print('Chain1: %s units long' % len(bot.markovchains[serv]))
        print('Chain2: %s units long' % len(bot.markovchains2[serv]))
        bot.corpus_last_read = time.time()
    else:
        print('Corpus is freshly loaded!')

    print('making a markov chain from server corpus: %s and seed: %s' % (serv, str(seed)))
    msg = cm.generate_message2(bot.markovchains[serv], bot.markovchains2[serv], seed=seed)
    print('made a 2nd order markov chain:\n%s' % msg)
    if msg is not None:
        await bot.say(msg)


def main():
    bot.run(token)

if __name__=='__main__':
    main()
