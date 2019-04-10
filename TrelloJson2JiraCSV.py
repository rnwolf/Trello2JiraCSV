#! /usr/bin/python

# MIT License

# Copyright (c) 2016 Harry Rose - Semaeopus Ltd.

# Permission is hereby granted, free of charge, to any person obtaining a copy
# of this software and associated documentation files (the "Software"), to deal
# in the Software without restriction, including without limitation the rights
# to use, copy, modify, merge, publish, distribute, sublicense, and/or sell
# copies of the Software, and to permit persons to whom the Software is
# furnished to do so, subject to the following conditions:

# The above copyright notice and this permission notice shall be included in all
# copies or substantial portions of the Software.

# THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
# IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
# FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
# AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
# LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
# OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE
# SOFTWARE.

import sys
reload(sys)
sys.setdefaultencoding('utf-8')

import json
import optparse

# Add an item to the csv row
# Will re-encode to utf8 and wrap quotes around text that contains quotes
def AddCSVItem(str):
	global csvData
	finalStr = str #.encode("utf8")
	finalStr = finalStr.replace("\"", "\"\"")
	csvData += "\"{0}\",".format(finalStr)

# Iterate a tasks checklist and generate subtasks
def AddCheckListAsSubTasks(checkListIDs, parentID):
	if not checkListIDs:
		return

	for checkListID in checkListIDs:
		for item in checklistDict[checkListID]:
			checkListName = checklistNames[checkListID]

			status = "Done" if item["state"] == "complete" else "To Do"
			resolution = "Done" if status == "Done" else ""
			summary = item["name"]

			if checkListName != 'Checklist':
				summary = checkListName + " - " + summary

			AddIssue("Sub-Task", "", parentID, status, reporter, asignee, resolution, summary,"", "", "", "", "", None, None)
			# def AddIssue(issuetype, IssueID, ParentID, Status, reporter, asignee, resolution, summary,
			# dateCreated, dateModified, description, attachments, component, labels, comments):

# End the csv row with a simple newline
def EndCSVLine():
	global csvData
	csvData += "\n"

def NickNameToUser(nickname):
	global nickNamesMap
	if nickNamesMap.get(nickname):
		return nickNamesMap.get(nickname)
	else:
		return nickname

# Take all the information for an issue and convert it into a csv line
def AddIssue(issuetype, IssueID, ParentID, Status, reporter, asignee, resolution, summary, dateCreated, dateModified, description, attachments, component, labels, comments):

## headerLine
## = "issuetype, Issue ID, Parent ID, Status, Resolution, summary, dateCreated, dateModified, description,
## component" + (", attachment" * maxAttachments) + (", label" * maxLabels) + (", comment" * maxComments) + "\n"

	AddCSVItem(issuetype)
	AddCSVItem(IssueID)
	AddCSVItem(ParentID)
	AddCSVItem(Status)
	AddCSVItem(resolution)
	AddCSVItem(summary)
	AddCSVItem(dateCreated)
	AddCSVItem(dateModified)
	AddCSVItem(description)
	AddCSVItem(component)

	# Handle attachments
	numAttachments = len(attachments) if attachments != None else 0
	if numAttachments > maxAttachments:
		print(f"\tError! - {numAttachments} Attachments found in \"{summary}\". Card will be skipped, only {maxAttachments} will be handled. Update header line and maxAttachments value")
		return 1

	for i in range(numAttachments):
		AddCSVItem(attachments[i]["url"])
	for i in range(numAttachments, maxAttachments):
		AddCSVItem("")

	numLabels = len(labels) if labels != None else 0
	if numLabels > maxLabels:
		print(f"\tError! - {numLabels} labels found in \"{summary}\". Card will be skipped, only {maxLabels} will be handled. Update header line and maxLabels value")
		return 1

	for i in range(numLabels):
		label = labels[i]["name"]
		label = label.replace(" ", "_")
		AddCSVItem(label)
	for i in range(numLabels, maxLabels):
		AddCSVItem("")


	numComments = len(comments) if comments != None else 0
	if numComments > numComments:
		print "\tError! - {0} comments found in \"{1}\". Comments will be skipped, only {1} will be handled. Update header line and maxComments value".format(numLabels, summary, maxLabels)
		return 1

	for i in range(numComments):
		comment = comments[i]
		AddCSVItem("{0};{1};{2} ({3}): {4};".format(comment["date"], NickNameToUser(comment["memberCreator"]["username"]), comment["memberCreator"]["fullName"], comment["memberCreator"]["username"] , comment["data"]["text"]))
	for i in range(numComments, maxComments):
		AddCSVItem("")


	EndCSVLine()

# Set up the parser for options
parser = optparse.OptionParser(version='TrelloJson2JiraCSV v1.0.0')

parser.add_option('-j', '--json'        , dest="jsonPath"   	, action="store"         , help="The path to the trello json file")
parser.add_option('--list_as_component' , dest="listAsComp"    	, action="store_true"    , help="Use the list as a component in Jira rather than setting it as a status", default=False)
parser.add_option('--usernames'			, dest="usersFile"		, action="store"		 , help="Provide the username mapping", default=False);

(opts, args) = parser.parse_args()

if not opts.jsonPath:
	parser.print_help()
	exit(1)

# Set up variables
jsonPath 		= opts.jsonPath
csvPath 		= jsonPath.replace(".json", ".csv")
listDict 		= {}
checklistDict 	= {}
checklistNames 	= {}
csvData 		= ""
maxLabels 		= 10
maxAttachments  = 10
maxComments		= 30
headerLine 		= "issuetype, Issue ID, Parent ID, Status, Resolution, summary, dateCreated, dateModified, description, component" + (", attachment" * maxAttachments) + (", label" * maxLabels) + (", comment" * maxComments) + "\n"
nickNamesMap 	= {}
if opts.usersFile:
	with open(opts.usersFile) as nickNamesMap:
		nickNamesMap = json.load(nickNamesMap)

print("Loading " + jsonPath)

# Load json data
with open(jsonPath) as data_file:
    data = json.load(data_file)

# Build up our list of list ids to names as trello items only contain ids, we'll use this to map between the two
for list in data["lists"]:
	listDict[list["id"]] = list["name"]

# Same as above to checklists, build up a id to name map
for checkList in data["checklists"]:
	checklistDict[checkList["id"]] = checkList["checkItems"]
	checklistNames[checkList["id"]] = checkList["name"]

# Dump some useful information about the board
print("Trello Board: {0} ({1})".format(data["name"], data["url"]))
print("\t{0} lists found".format(len(data["lists"])))
print("\t{0} cards found".format(len(data["cards"])))
print("\t{0} checklists found".format(len(data["checklists"])))
print("\t{0} labels found".format(len(data["labels"])))

# Core loop
for card in data["cards"]:
	# Grab all the core data we'll need from the card
	issueID 	= card["id"]
	cardName 	= card["name"].rstrip()
	dateModified= card["dateLastActivity"].rstrip()
	dateCreated = dateModified
	shortURL 	= card["shortUrl"].strip()
	labels 		= card["labels"]
	listName 	= listDict[card["idList"]]
	attachments = card["attachments"]
	comments	= []
	status 		= "To Do"
	component 	= ""
	reporter 	= ""



	if  len(card["labels"]):
		component = card["labels"][0]["name"]
		cardDesc = "Labels: "
		for label in card["labels"]:
			cardDesc += label["name"].rstrip() + ", "
	else:
		cardDesc = "Labels: empty\n\n"


	# We'll use the list name as the status of component depending on user input
	if opts.listAsComp:
		component = listName
	else:
		status 	  = listName


	if card["closed"] == True:
		status = "Archived"

	# Set resolution up value if we can
	resolution = "Done" if status == "Done" else ""

	# Append URL to description
	if cardDesc:
		cardDesc += "\n\nGenerated from: " + shortURL
	else:
		cardDesc = "Generated from: " + shortURL


	# Find comments
	for action in data["actions"]:
		if action["type"] == "commentCard":
			if action["data"]["card"]["id"] == issueID :
				comments.append(action)
		elif action["type"] == "createCard":
			if action["data"]["card"]["id"] == issueID :
				dateCreated = action["date"]
				memberCreator = NickNameToUser(action["memberCreator"]["username"])

	asignee = ""


	AddIssue("task", issueID, "", status, reporter, asignee, resolution, cardName, dateCreated, dateModified, cardDesc, attachments, component, labels, comments)
	# def AddIssue(issuetype, IssueID, ParentID, Status, reporter, asignee, resolution, summary,
	# dateCreated, dateModified, description, attachments, component, labels, comments):

	AddCheckListAsSubTasks(card["idChecklists"], issueID)

# Write out csv file
with open(csvPath, "w") as csvFile:
	csvFile.write(headerLine)
	csvFile.write(csvData)
	print(f"\tData written to {csvPath}")
