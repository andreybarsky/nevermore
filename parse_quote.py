def qparse(msg, user):
    """Takes discord message content and cleans it up into a single or multiline string"""

    #fullquote = msg.split(user + ' ')[1]

    #now split into lines:
    lines = msg.split('\n')

    cleaned_lines = []
    #and check for multi-user quotes

    # iterate through lines and build new ones:
    #newline = user + ": "
    newline = ""
    for l in lines:
        if 'Today at' in l:
            new_user = l.split(' - Today')[0]
            newline = new_user + ": "
        elif 'NEW MESSAGES' in l:
            pass
        else:
            newline += l
            cleaned_lines.append(newline)
            newline = ""
    return '\n'.join(cleaned_lines)

