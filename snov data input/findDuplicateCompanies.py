import shutil


previousCompaniesFile = "./previousCompanyNames.txt"
newCompaniesFile = "./newCompanyNames.txt"
backupPreviousCompaniesFile = "./previousCompanyNames.backup"
backupPreviousCompaniesFile2 = "./previousCompanyNames.backup2"
numberOfCharacters = 4

previousNames = open(previousCompaniesFile, "r").read().split("\n")
newNames = open(newCompaniesFile, "r").read().split("\n")

previousNamesFirstChars = {}
for name in previousNames:
    firstChars = name[:numberOfCharacters].lower()
    if firstChars in previousNamesFirstChars:
        previousNamesFirstChars[firstChars].append(name)
    else:
        previousNamesFirstChars[firstChars] = [name]

nonDuplicateNewNames = []

for name in newNames:
    dupe = False
    firstChars = name[:numberOfCharacters].lower()
    if firstChars in previousNamesFirstChars:
        for previousName in previousNamesFirstChars[firstChars]:
            print("\n\nOLD: " + previousName)
            duplicate = input("NEW: " + name + "   DUP (d)?")
            if duplicate.lower() != "":
                dupe = True
    if not dupe:
        nonDuplicateNewNames.append(name)


shutil.copyfile(backupPreviousCompaniesFile,backupPreviousCompaniesFile2)
shutil.copyfile(previousCompaniesFile,backupPreviousCompaniesFile)


nonDuplicateNewNameString = "\n" + "\n".join(nonDuplicateNewNames)
previousNamesFile = open(previousCompaniesFile, 'a')
previousNamesFile.write(nonDuplicateNewNameString)
previousNamesFile.close()

print(nonDuplicateNewNameString)