import string

## some utility functions for handling quotes and filenames

def qparse(msg, user):
    """Takes discord message content and cleans it up into a single or multiline string"""

    #now split into lines:
    lines = msg.split('\n')
    print('Parsing multiline message:')
    print(msg)
    print('Split lines:')
    print(lines)

    cleaned_lines = []
    #and check for multi-user quotes

    # iterate through lines and build new ones:
    #newline = user + ": "
    newline = ""
    for l in lines:
        if 'Today at' in l:
            print('Stripping out time line, adding username:')
            print(l)
            new_user = l.split(' - Today')[0]
            new_user = new_user.replace('BOT', '') # strip out BOT tag
            newline = '<%s>' % new_user
            print('newline is:')
            print(newline)
        elif 'NEW MESSAGES' in l:
            print('Stripping out new messages:')
            print(l)
            pass
        else:
            print('Appending new line to current user')
            print(l)
            newline += l
            cleaned_lines.append(newline)
            newline = ""
    return '\n'.join(cleaned_lines)

def to_filename(text):
    """Turns a text string into a valid filename"""
    valid_chars = "-_.()%s%s" % (string.ascii_letters, string.digits)
    text = text.replace(' ', '_') # replace spaces
    newtext = ''.join(c for c in text if c in valid_chars)
    if newtext == '':
        newtext = 'misc_server'
    return newtext

def is_number(x):
    """Checks if a string can be converted to int"""
    try:
        num = int(x)
    except ValueError:
        return False
    return True