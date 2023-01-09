from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
from datetime import datetime
from pandas import Timestamp
import traceback
import imaplib
import smtplib
import jinja2
import random
import copy
import time
import json
import csv
import sys
import os


def getConfig():
    configFileName = "config.json"
    with open(configFileName) as config:
        return json.load(config)


def str2bool(v):
    return json.loads(str(v).lower())


def smtpStart():
    username = getConfig()["auth"]["username"]
    password = getConfig()["auth"]["password"]
    try:
        server = smtplib.SMTP_SSL("smtp.gmail.com", 465)
        server.ehlo()
        server.login(username, password)
    except:
        errorMessage = str([str(traceback.format_exc()), str(sys.exc_info())])
        addLog("smtpStart", "", errorMessage, "")

    return server


def trimLogFile():
    n = random.random()
    if n > 1 / 1000:
        return
    maxLogFileLength = getConfig()["maxLogFileLength"]
    logFile = getConfig()["logFile"]
    with open(logFile, "w") as log:
        lines = log.read().strip("\n").split("\n")
        revisedLines = lines[-maxLogFileLength:]
        log.write("\n".join(revisedLines))
    addLog("trimLogFile", "", "", "")


def addLog(process, contact, errorMessage, listIndex):
    now = datetime.now()
    currentDateTime = now.strftime("%d/%m/%Y %H:%M:%S")
    logFile = getConfig()["logFile"]
    if os.path.exists(logFile):
        fileMode = "a"  # append if already exists
    else:
        fileMode = "w"  # make a new file if not
    logEntry = {
        "process": process,
        "contact": contact,
        "error": errorMessage,
        "stage": listIndex,
        "dateTime": currentDateTime,
    }
    with open(logFile, fileMode) as log:
        log.write("\n" + str(logEntry))
    if errorMessage:
        for error in eval(errorMessage):
            print(error)
        print(currentDateTime)


def sleepBetweenCycles():
    addLog("sleepBetweenCycles", "", "", "")
    daemonSleepInterval = getConfig()["daemonSleepInterval"]
    time.sleep(daemonSleepInterval)


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


def addContactToList(contact, filePath):
    contactList = getContactList(filePath)
    contactList.append(contact)
    writeContactList(contactList, filePath)


def removeContactFromList(contactToRemove, filePath):
    contactList = getContactList(filePath)
    revisedContactList = []
    for contact in contactList:
        if contact["email"].lower() != contactToRemove["email"].lower():
            revisedContactList.append(contact)

    writeContactList(revisedContactList, filePath)


def getDeletedDomains():
    deletedDomainsFile = getConfig()["deletedDomainsFile"]

    with open(deletedDomainsFile) as deletedDomains:
        deletedDomains = deletedDomains.read().strip().lower().split("\n")
        return deletedDomains


def addDeletedDomain(domain):
    alreadyDeletedDomains = getDeletedDomains()
    if domain.lower() in alreadyDeletedDomains:
        return
    addLog("addDeletedDomain", domain, "", "")
    deletedDomainsFile = getConfig()["deletedDomainsFile"]
    with open(deletedDomainsFile, "a") as deletedDomains:
        deletedDomains.write(domain.lower() + "\n")


def lastAddedNew(action):
    lastAddedNewFile = getConfig()["lastAddedNewFile"]
    if action == "update":
        currentTime = time.time()
        with open(lastAddedNewFile, "w") as lastAddedNew:
            lastAddedNew.write(str(currentTime))
    if action == "get":
        with open(lastAddedNewFile, "r") as lastAddedNew:
            return int(lastAddedNew.read().strip().split(".")[0])


def isPastTime(timeString):
    currentTime = Timestamp.now().timestamp()
    comparisonTime = Timestamp(timeString).timestamp()
    secondsOverdue = currentTime - comparisonTime
    isOverdue = secondsOverdue >= 0
    return isOverdue


def addNewContacts():
    firstOutReachTime = getConfig()["firstOutReachMondayTime"]
    currentTime = time.time()
    newOutreachDay = getConfig()["newOutreachDay"]
    lastAddedNewTime = lastAddedNew("get")
    isNotNewOutreachDay = datetime.today().weekday() != newOutreachDay
    notPastOutreachTime = not isPastTime(firstOutReachTime)
    recentlyAddedAlready = (currentTime - lastAddedNewTime) < 60 * 60 * 25
    if isNotNewOutreachDay or recentlyAddedAlready or notPastOutreachTime:
        return

    addLog("addNewContacts", "", "", "")
    newContactsFile = getConfig()["inactiveContactFiles"]["new"]
    newContacts = getContactList(newContactsFile)
    contactsPerWeek = getConfig()["contactsPerWeek"]

    contactsToAdd = []
    for contact in newContacts[:contactsPerWeek]:
        contact["addedTime"] = 0
        contact["newlyAdded"] = True  # signifies that it hasn't been outreached yet
        contactsToAdd.append(contact)

    lastAddedNew("update")
    firstOutreachFile = getConfig()["activeContactFiles"][0]
    firstOutreachContacts = getContactList(firstOutreachFile)
    firstOutreachContacts.extend(contactsToAdd)
    writeContactList(firstOutreachContacts, firstOutreachFile)

    revisedNewContacts = newContacts[contactsPerWeek:]
    writeContactList(revisedNewContacts, newContactsFile)


def removeEmailorDomainFromLists(emailOrDomain, contactType):
    foundContactToBeDeleted = False
    newContactsFile = getConfig()["inactiveContactFiles"]["new"]
    activeContactFiles = getConfig()["activeContactFiles"]
    deletedContactsFile = getConfig()["inactiveContactFiles"]["deleted"]
    activeContactFiles.append(newContactsFile)
    newDeletedContacts = []

    for index, contactFile in enumerate(activeContactFiles):
        contactList = getContactList(contactFile)
        revisedContactList = []
        for contact in contactList:
            if contactType == "email":
                if contact["email"].lower() != emailOrDomain:
                    revisedContactList.append(contact)
            if contactType == "domain":
                if contact["email"].split("@")[1].lower() != emailOrDomain:
                    revisedContactList.append(contact)
                else:
                    addDeletedDomain(emailOrDomain)
            if contact not in revisedContactList:
                addLog("deleteContact", contact, "", index)
                foundContactToBeDeleted = True
                contact["outreachStage"] = index
                contact["deletedTime"] = datetime.now().strftime("%d/%m/%Y %H:%M:%S")
                newDeletedContacts.append(contact)

        writeContactList(revisedContactList, contactFile)

    deletedContacts = getContactList(deletedContactsFile)
    deletedContacts.extend(newDeletedContacts)
    writeContactList(deletedContacts, deletedContactsFile)
    return foundContactToBeDeleted


def renderTemplate(template, substitutionParams):
    templ = jinja2.Template(open(template).read())
    return templ.render(substitutionParams)


def sendEmail(emailObject):
    server = smtpStart()
    if type(emailObject["to"]) is not list:
        emailObject["to"] = emailObject["to"].split()

    to_list = (
        emailObject["to"]
        + [emailObject.get("cc", None)]
        + [emailObject.get("bcc", None)]
    )

    to_list = list(filter(None, to_list))  # remove null emails

    msg = MIMEMultipart("alternative")
    msg["To"] = ",".join(emailObject.get("to"))
    msg["From"] = emailObject.get("from")
    msg["Subject"] = emailObject.get("subject", None)
    msg["Cc"] = emailObject.get("cc", None)
    msg["Bcc"] = emailObject.get("bcc", None)
    msg.add_header("reply-to", emailObject.get("replyToAddress", msg["From"]))
    msg.attach(MIMEText(emailObject.get("body"), "html"))
    server.sendmail(emailObject.get("from"), to_list, msg.as_string())


def sendOutreach(outReachPhase, contact):
    username = getConfig()["auth"]["username"]
    replyToAddress = getConfig()["replyToAddress"]
    templateFile = getConfig()["templateFiles"][outReachPhase]
    substitutionParams = copy.deepcopy(contact)
    substitutionParams["senderName"] = getConfig()["senderName"]
    substitutionParams["senderEmail"] = username
    bodyHtml = renderTemplate(templateFile, substitutionParams)
    emailObject = {}
    emailObject["to"] = contact["email"]
    emailObject["from"] = username
    emailObject["subject"] = getConfig()["subjects"][outReachPhase]
    emailObject["body"] = bodyHtml
    emailObject["replyToAddress"] = replyToAddress
    errorMessage = ""
    try:
        sendEmail(emailObject)
    except:
        errorMessage = str([str(traceback.format_exc()), str(sys.exc_info())])

    addLog("sendOutreach", contact, errorMessage, outReachPhase)
    return True if errorMessage else False


def checkDeleteRequests():
    username = getConfig()["auth"]["username"]
    password = getConfig()["auth"]["password"]
    imap = imaplib.IMAP4_SSL("imap.gmail.com")
    imap.login(username, password)
    typ, data = imap.select("INBOX")
    typ, data = imap.search(None, 'HEADER Subject "deletecontact"')
    for num in data[0].split():
        typ, data = imap.fetch(num, "(RFC822.SIZE BODY[HEADER.FIELDS (SUBJECT)])")
        num = int(num) + 1
        subject = data[0][1].decode("utf8").lstrip("Subject: ").strip()
        argList = subject.split(" ")
        if argList[0] == "" or argList[0] == " ":
            del argList[0]  # idk why this is necessary... maybe it isn't
        contactsToDelete = argList[1:]
        validCommand = argList[0].lower() == "deletecontact"
        if not validCommand:
            continue
        for contact in contactsToDelete:
            contact = contact.lower().strip()
            noProtocol = ("http" not in contact) and ("www." not in contact)
            dotInContact = "." in contact
            contactType = "email" if "@" in contact else "domain"
            if noProtocol and validCommand and dotInContact:
                deletedMatch = removeEmailorDomainFromLists(contact, contactType)
                if deletedMatch:
                    imap.store(str(num - 1), "+FLAGS", "\\Deleted")

    imap.expunge()
    imap.close()
    imap.logout()


def tryCheckDeleteRequests():
    try:
        errorMessage = ""
        checkDeleteRequests()
    except:
        errorMessage = str([str(traceback.format_exc()), str(sys.exc_info())])
    addLog("checkDeleteRequests", "", errorMessage, "")


def outreachAllContacts():
    addLog("outreachAllContacts", "", "", "")
    activeContactFiles = getConfig()["activeContactFiles"]
    waitingPeriods = getConfig()["waitingPeriods"]
    currentTime = time.time()
    contactsToMove = {i: [] for i in range(len(activeContactFiles))}
    delayBetweenEmails = getConfig()["delayBetweenEmails"]

    for listIndex, contactFile in enumerate(activeContactFiles[:-1]):
        contactList = getContactList(contactFile)
        outreachWaitingPeriod = int(waitingPeriods[listIndex])
        revisedContactList = []
        for contact in contactList:
            addedTime = int(contact["addedTime"].split(".")[0])
            outreachDue = addedTime + outreachWaitingPeriod <= currentTime
            newlyAdded = str2bool(contact["newlyAdded"])  # csv returns bools as strings
            if newlyAdded:
                contact["addedTime"] = currentTime
                sendingError = sendOutreach(listIndex, contact)
                if not sendingError:
                    contact["newlyAdded"] = False
                    removeContactFromList(contact, contactFile)
                    addContactToList(
                        contact, contactFile
                    )  # to update its addedTime field
                    time.sleep(delayBetweenEmails)
            elif outreachDue:
                contact["addedTime"] = currentTime
                sendingError = sendOutreach(listIndex + 1, contact)
                if not sendingError:
                    removeContactFromList(contact, contactFile)
                    addContactToList(contact, activeContactFiles[listIndex + 1])
                    time.sleep(delayBetweenEmails)


def removeDuplicateNewContacts():
    addLog("removeDuplicateNewContacts", "", "", "")
    activeContactFiles = getConfig()["activeContactFiles"]
    deletedContactsFile = getConfig()["inactiveContactFiles"]["deleted"]
    activeContactFiles.append(deletedContactsFile)

    newContactsFile = getConfig()["inactiveContactFiles"]["new"]
    newContacts = getContactList(newContactsFile)
    newContactEmails = [newContact["email"].lower() for newContact in newContacts]
    duplicatNewContactIndexes = []
    deleteOccured = False

    for index, contactFile in enumerate(activeContactFiles):
        contactList = getContactList(contactFile)
        for contact in contactList:
            contactEmail = contact["email"].lower()
            if contactEmail in newContactEmails:
                indexOfDuplicateNewContact = newContactEmails.index(contactEmail)
                duplicatNewContactIndexes.append(indexOfDuplicateNewContact)

    deletedDomains = getDeletedDomains()
    internallyDuplicateNewContacts = [
        idx for idx, val in enumerate(newContactEmails) if val in newContactEmails[:idx]
    ]
    duplicatNewContactIndexes.extend(internallyDuplicateNewContacts)

    revisedNewContacts = []
    for i, contact in enumerate(newContacts):
        emailDomain = contact["email"].split("@")[1].lower()
        if (i not in duplicatNewContactIndexes) and (emailDomain not in deletedDomains):
            revisedNewContacts.append(contact)
        else:
            addLog("removeDuplicateNewContacts", contact, "", 4)
            deleteOccured = True
    if deleteOccured:
        writeContactList(revisedNewContacts, newContactsFile)


while True:
    removeDuplicateNewContacts()
    tryCheckDeleteRequests()
    addNewContacts()
    outreachAllContacts()
    sleepBetweenCycles()
