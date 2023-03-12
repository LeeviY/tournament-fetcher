import mailbox
import os
import re

#ids = set()
#fails = []
#cwd = os.getcwd()
#mbox = mailbox.mbox(cwd + "\Inbox.mbox")
#for i, message in enumerate(mbox):
#    if message["from"] == "<jouko.huovinen@kolumbus.fi>":
#        for part in message.get_payload():
#            payload = part.get_payload()
#            if type(payload) == list:
#                fails.append(message["Date"])
#                continue
#            links = re.findall("worldoftanks.eu\/en\/tournaments\/[0-9]+", payload)
#            print(links)
#            for link in links:
#                id = link.split("/")[-1]
#                print(id)
#                ids.add(id)
#
#print(ids)
#print(fails)
#
ids = set()

with open("Inbox.mbox", "r", encoding="utf-8") as mail:
    all_mail = mail.read()
    links = re.findall("worldoftanks.eu\/en\/tournaments\/[0-9]+", all_mail)
    for link in links:
        id = link.split("/")[-1]
        print(id)
        ids.add(id)

a = sorted(list(ids), key=lambda x: int(x), reverse=True)

with open("ids.txt", "w+") as outfile:
    [outfile.write(id + "\n") for id in a]