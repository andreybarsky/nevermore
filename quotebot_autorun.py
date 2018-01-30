import logging
import socket
import sys

lock_socket = None  # we want to keep the socket open until the very end of
                    # our script so we use a global variable to avoid going
                    # out of scope and being garbage-collected

def is_lock_free():
    global lock_socket
    lock_socket = socket.socket(socket.AF_UNIX, socket.SOCK_DGRAM)
    try:
        lock_id = "doubtfulguest.nevermore"   # this should be unique. using your username as a prefix is a convention
        lock_socket.bind('\0' + lock_id)
        print("Acquired lock %r" % (lock_id,))
        return True
    except socket.error:
        # socket already locked, task must already be running
        print("Failed to acquire lock %r" % (lock_id,))
        return False

if not is_lock_free():
    print('Exiting.')
    sys.exit()

from quotebot import main
main()