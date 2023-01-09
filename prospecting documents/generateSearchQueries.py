queriesList = input("Queries: ").split(",")


urlList = []
for query in queriesList:
    newUrlList = []
    for i in range(1, 10):
        newUrlList.append(
            "https://www.startpage.com/sp/search?query="
            + 'inurl:crunchbase.com/organization intext:("'
            + query
            + '" AND "data")'
            + "&page="
            + str(i)
        )
        newUrlList.append(
            "https://www.startpage.com/sp/search?query="
            + 'inurl:linkedin.com/company intext:("'
            + query
            + '" AND "data")'
            + "&page="
            + str(i)
        )
    urlList.extend(newUrlList)

print("\n".join(urlList))
