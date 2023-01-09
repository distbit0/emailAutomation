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


outputCompanies = getContactList("./outputCompanies.csv")
outputContacts = getContactList("./outputContacts.csv")


companiesList = {}
for company in outputCompanies:
    companiesList[company["company"]] = company

revisedContactList = []

for contact in outputContacts:
    company = companiesList[contact["company"]]
    revisedContact = copy.deepcopy(contact)
    revisedContact["apiType"] = company["apiType"]
    revisedContact["sector"] = company["sector"]
    revisedContact["url"] = company["url"]
    revisedContactList.append(revisedContact)


writeContactList(revisedContactList, "revisedContacts.csv")
