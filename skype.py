import Skype4Py
from urllib import urlopen

HOST = "127.0.0.1"
PORT = 8000
USER = "undefined"

def user_status(Status):
        print("User status changed to {0}".format(Status))
        urlopen("http://{0}:{1}/skype?id={2}&status={3}".format(HOST, PORT, USER, Status))


# Create an instance of the Skype class.
skype = Skype4Py.Skype()

# Connect the Skype object to the Skype client.
skype.Attach()

USER = skype.CurrentUser.Handle

skype.OnUserStatus = user_status

print("Skype status notifier running in a loop. Hit CTRL-C to quit.")

import time
while True:
    time.sleep(1)
