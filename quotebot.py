# updated

import discord, asyncio
from discord.ext import commands
import logging
import time
import random

import quote_manager as qm
import tag_manager as tm
import corpus_manager as cm

from quote_utils import qparse, to_filename, is_number

token = 'NDA0MjIyMTM0OTQ5MzgwMTA2.DUSzYg.OUrC1agKwJOsRJV9uLsRgSeN67U'
description = None

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

    if serv is not None:
        tags = tm.TagBank(serv) # get tags
        tagstring = tags.gettags(name.lower())
        if tagstring == 'No tags.':
            return name
        else:
            taglist = tagstring.split(', ')
            possible_names = [name] + taglist # list of real name and tags
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

    bot.markovchains = {}
    bot.corpus_last_read = 0

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
            quotes.to_xml()
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
            await bot.say('Tag added.')

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
    # if we haven't loaded the chain for this server, or if we haven't loaded one in a while:
    if serv not in bot.markovchains or time.time() - bot.corpus_last_read > (60*60):
        print('Loading corpus from %s' % serv)
        bot.markovchains[serv] = cm.server_chain(serv)
        print('The result chain is %s units long' % len(bot.markovchains[serv]))
        bot.corpus_last_read = time.time()

    if seed == ():
        seed = ['END']

    msg = cm.generate_message(bot.markovchains[serv], seed=seed)
    await bot.say(msg)

@bot.event
async def on_message(message):
    # we do not want the bot to reply to itself
    if message.author != bot.user:
        cmd = message.content.lower()
        serv = to_filename(str(message.server))

        if time.time() - bot.last_reply > 60: # 60 sec cooldown
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
            elif 'cast bot' in cmd: # a dominions in-joke
                msgs = ["cast what now?",
                        "better not cast that.",
                        "leave me out of this."]
                msg = random.choice(msgs)

            else:
                msg = None

            if msg is not None:
                bot.last_reply = time.time()
                await bot.send_message(message.channel, msg)

        # record raw messages to corpus:
        cm.write(cmd, serv)

    await bot.process_commands(message)


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

def main():
    bot.run(token)

if __name__=='__main__':
    main()
