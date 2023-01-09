import copy
import csv


def getContactList(filePath):
    with open(filePath) as f:
        contactList = [
            {str(k): str(v) for k, v in row.items()}
            for row in csv.DictReader(f, skipinitialspace=True)
        ]
    return contactList


def writeContactList(contactList, filePath):
    keys = contactList[0].keys() if contactList else []
    with open(filePath, "w", newline="") as output_file:
        dict_writer = csv.DictWriter(output_file, keys)
        dict_writer.writeheader()
        dict_writer.writerows(contactList)


revisedContacts = getContactList("./revisedContacts.csv")
stage3contacts = open("./stage3contacts.txt").read().strip().split("\n")


contactsList = {}
for contact in revisedContacts:
    contactsList[contact["email"].lower()] = contact

stage3ContactsList = []
for contact in stage3contacts:
    revisedContact = contactsList[contact.lower()]
    stage3ContactsList.append(revisedContact)

writeContactList(stage3ContactsList, "revisedStage3Contacts.csv")
