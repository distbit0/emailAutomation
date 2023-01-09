import csv
import copy

folderPath = "/home/pimania/Dev/busDevEmail/snov data export"
prospectFile = folderPath + "/new111.csv"
companyOutputFile = folderPath + "/outputCompaniesForSF.csv"
contactsOutputFile = folderPath + "/outputContactsForSF.csv"


def delEntriesFromDict(entries, the_dict):
    for key in entries:
        if key in the_dict:
            del the_dict[key]
    return the_dict


def getProspectData(filePath):
    with open(filePath) as f:
        prospectData = [
            {str(k): str(v) for k, v in row.items()}
            for row in csv.DictReader(f, skipinitialspace=True)
        ]
    return prospectData


def modifyProspectDataColumns(prospectData):
    modifiedProspectData = []
    for prospect in prospectData:
        modifiedProspect = {}
        modifiedProspect["company"] = prospect["company"]
        modifiedProspect["first"] = prospect["first"]
        modifiedProspect["last"] = prospect["last"]
        modifiedProspect["position"] = prospect["position"]
        modifiedProspect["email"] = prospect["email"]
        modifiedProspect["description"] = (
            "A company that provides an API relating to " + prospect["sector"] + "."
        )
        modifiedProspect["sector"] = prospect["sector"]
        modifiedProspect["apiType"] = prospect["apiType"]
        modifiedProspect["url"] = prospect["url"]
        modifiedProspectData.append(modifiedProspect)
    return modifiedProspectData


def saveContactListAsCSV(prospectData, contactsOutputFile):
    newProspectList = []
    for prospect in prospectData:
        newProspect = copy.deepcopy(prospect)
        newProspect = delEntriesFromDict(
            ["apiType", "url", "sector", "description"], newProspect
        )
        newProspectList.append(newProspect)

    keys = ["company", "first", "last", "position", "email"]
    with open(contactsOutputFile, "w", newline="") as output_file:
        dict_writer = csv.DictWriter(output_file, keys)
        dict_writer.writeheader()
        dict_writer.writerows(newProspectList)


def saveCompanyListAsCSV(prospectData, companyOutputFile):
    includedCompanies = []
    revisedProspects = []
    for prospect in prospectData:
        if not prospect["company"] in includedCompanies:
            includedCompanies.append(prospect["company"])
            revisedProspects.append(prospect)

    keys = [
        "company",
        "description",
        "apiType",
        "sector",
        "url",
        "first",
        "last",
        "position",
        "email",
    ]
    with open(companyOutputFile, "w", newline="") as output_file:
        dict_writer = csv.DictWriter(output_file, keys)
        dict_writer.writeheader()
        dict_writer.writerows(revisedProspects)


prospectData = getProspectData(prospectFile)
modifiedProspectData = modifyProspectDataColumns(prospectData)
saveContactListAsCSV(modifiedProspectData, contactsOutputFile)
saveCompanyListAsCSV(modifiedProspectData, companyOutputFile)
