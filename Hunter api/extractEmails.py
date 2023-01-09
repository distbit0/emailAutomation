import csv
import requests
import copy
import time
import traceback
import sys
import json

filePath = "./companyData.csv"
apiKey = ""
companyOutputFile = "./outputCompanies.csv"
contactsOutputFile = "./outputContacts.csv"
sleepBetweenRequests = 1/13

def removeAPIFromString(s):
    wordList = s.split()
    i = 0
    while i < len(wordList):
        if wordList[i].lower() == "api" or wordList[i].lower() == "apis":
            del wordList[i]
        else:
            i+=1
    s = ' '.join(wordList)
    return s

def delEntriesFromDict(entries, the_dict):
    for key in entries:
        if key in the_dict:
            del the_dict[key]
    return the_dict

def getCompanyData(filePath):
    with open(filePath) as f:
        companyData = [{str(k): str(v) for k, v in row.items()}
            for row in csv.DictReader(f, skipinitialspace=True)]
    return companyData

def getCompanyContactInfo(url, apiKey):
    errors = []
    contactList = []
    contactInfo = []

    try:
        companyData = requests.get("https://api.hunter.io/v2/domain-search?domain=" + url + "&api_key=" + apiKey).json()
        contactList = companyData["data"]["emails"]
    except Exception:
        errors.append([str(traceback.format_exc()), str(sys.exc_info()), url])

    try:
        for contact in contactList:
            currentContact = {}
            currentContact["first"] = str(contact["first_name"])
            currentContact["last"] = str(contact["last_name"])
            currentContact["position"] = str(contact["position"])
            currentContact["email"] = str(contact["value"])
            contactInfo.append(currentContact)
    except Exception:
        errors.append([str(traceback.format_exc()), str(sys.exc_info()), url])

    return contactInfo, errors

def getContactsForCompanies(companyData, filePath, apiKey, sleepBetweenRequests):
    contactList = []
    allErrors= []
    for company in companyData:
        contactInfo, errors = getCompanyContactInfo(company["DOMAIN"], apiKey)
        allErrors.extend(errors)
        for contact in contactInfo:
            completedContact = copy.deepcopy(contact)
            companyType = company["TYPE"].lower().replace("audiencemarketing", "audience marketing")
            completedContact["company"] = company["NAME"]
            completedContact["api type"] = companyType
            completedContact["sector"] = removeAPIFromString(companyType)
            completedContact["url"] = company["DOMAIN"]
            completedContact["description"] = ""
            contactList.append(completedContact)
        time.sleep(sleepBetweenRequests)
    return contactList, allErrors


def saveContactListAsCSV(contactList, contactsOutputFile):
    newContactList = []
    for contact in contactList:
        newContact = copy.deepcopy(contact)
        newContact = delEntriesFromDict(["api type", "url", "sector", "description"], newContact)
        newContactList.append(newContact)
    
    keys = ["company", "first", "last", "position", "email"]
    with open(contactsOutputFile, 'w', newline='')  as output_file:
        dict_writer = csv.DictWriter(output_file, keys)
        dict_writer.writeheader()
        dict_writer.writerows(newContactList)


def saveCompanyListAsCSV(contactList, companyOutputFile):
    includedCompanies = []
    revisedContacts = []
    for contact in contactList:
        if not contact["company"] in includedCompanies:
            includedCompanies.append(contact["company"])
            revisedContacts.append(contact)

    keys = ["company", "description", "api type", "sector", "url", "first", "last", "position", "email"]
    with open(companyOutputFile, 'w', newline='')  as output_file:
        dict_writer = csv.DictWriter(output_file, keys)
        dict_writer.writeheader()
        dict_writer.writerows(revisedContacts)

companyData = getCompanyData(filePath)
contactList, allErrors = getContactsForCompanies(companyData, filePath, apiKey, sleepBetweenRequests)
saveContactListAsCSV(contactList, contactsOutputFile)
saveCompanyListAsCSV(contactList, companyOutputFile)

print("Errors:\n" + json.dumps(allErrors, sort_keys=True, indent=4))
