import discord, asyncio
from discord.ext import commands
import logging
import time

import quote_manager as qm
import tag_manager as tm
import corpus_manager as cm

from quote_utils import qparse, to_filename, is_number

token = 'NDA0MjIyMTM0OTQ5MzgwMTA2.DUSzYg.OUrC1agKwJOsRJV9uLsRgSeN67U'
description = None

bot = commands.Bot(command_prefix='.', description=description)
bot.remove_command('help')

# features to be added:
# name and shame self quote abusers
# and self taggers

tags = tm.TagBank('discord')
last_reply = 0

@bot.event
async def on_ready():
    print('Logged in as')
    print(bot.user.name)
    print(bot.user.id)
    print('------')

    bot.last_reply = 0

    print([str(x) for x in bot.servers])

@bot.command(pass_context=True)
async def logg(ctx):
    print([x.content for x in bot.messages])

@bot.command(pass_context=True)
async def q(ctx, arg1 : str, *words : str):
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

        else:
            fullmsg = ctx.message.content # have to parse the full message to preserve newlines
            msg = fullmsg.split(user + ' ')[1] # separate out the .q add

        quote = qparse(msg, user)

        print('Adding quote:\n%s::%s' % (user, quote))
        quotes.add(user, quote)
        quotes.to_xml()

        await bot.say('Quote added.')

    else:
        # say a quote
        if arg1 == 'all': # grab a quote irrespective of user

            q = quotes.allquote()

        else: # grab a random quote from the named user
            user = arg1
            if '|' in words: # detect multi line usernames
                user, words = (' '.join(words)).split(' | ')

            if len(words) > 0: # we've been asked for an index, or a multi line username, or both
                if is_number(words[-1]): # there is an index
                    idx = int(words[-1]) # retrieve index

                    words = words[:-1]
                    if len(words) > 0: # are we dealing with a multi word username?
                        user = "%s %s" % (user, ' '.join(words)) # complete the username
                    #print("user: %s" % user)
                    #print("words: %s" % words)
                    q = quotes.get(user, idx) # multi word username with index
                else: # no index, just a multi word username on its own
                    user = "%s %s" % (user, ' '.join(words))
                    #print("user: %s" % user)
                    #print("words: %s" % words)
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
    else:
        tag = ' '.join(tag) # extract string from 1-tuple

    serv = to_filename(str(ctx.message.server))

    print('server name: %s' % serv)
    tags = tm.TagBank(serv)

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

    tags = tm.TagBank(serv)
    tagstring = tags.gettags(user)
    await bot.say("%s: %s" % (user, tagstring))

@bot.command(pass_context = True)
async def tagged(ctx, *tag : str):
    """<tag>: Show everyone who is tagged as this."""
    serv = to_filename(str(ctx.message.server))
    print(tag)
    tag = ' '.join(tag)
    tags = tm.TagBank(serv)
    userstring = tags.gettagged(tag)
    await bot.say("%s: %s" % (tag, userstring))

@bot.event
async def on_message(message):
    # we do not want the bot to reply to itself
    cmd = message.content.lower()
    serv = str(message.server)

    if time.time() - bot.last_reply > 60 and message.author != bot.user: # 20 sec cooldown
        if 'bad bot' in cmd:
            msg = ':('
        elif 'good bot' in cmd:
            msg = ':)'
        elif cmd in ['hello bot', 'hi bot']:
            name = message.author.nick
            if name is None:
                name = str(message.author).split('#')[0]
            msg = 'hi %s' % name
        elif 'cast bot' in cmd:
            msg = "cast what now?"
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
.q <name> [<idx>]: Retrieves a random quote from someone, optionally indexed by a number.
.tag <name> <tag>: Adds a tag to someone.
    or: .tag <long name> | <tag>
.tags <name>: Shows the tags for someone.
.tagged <tag>: Shows everyone with this tag.

"""
    await bot.say(helpstr)

bot.run(token)