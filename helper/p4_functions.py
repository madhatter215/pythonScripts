import subprocess
import helper.myfunc as myUtils         # local app: keep common functions there
from datetime import datetime
import re
from setup.config import *

try:
    db,cursor   = getDB()
except NameError:
    print ("**NOTE: No SQL connection, need db, cursor if using database commands\n\n")

#######################Json Keys#################################
JNAME_SQL       = 'SqlQueryCollection'
data            = myJsonData
#############

#os.environ['PATH'] += os.pathsep + '/pkg/qct/software/p4'
#os.environ['P4PORT'] = "p2.qca.qualcomm.com:1666"

P4CLIENT_TEMPLATE = \
"""
Client: {prefix}

Owner:  {user}

Description:
        Auto-Create label test

Root:   {projectsHome}

Options:        noallwrite noclobber nocompress unlocked nomodtime normdir

SubmitOptions:  submitunchanged

LineEnd:        local

View:
        {depotIpTop}/... //{prefix}/...

"""

########################################################################
# Function Definitions:
########################################################################

def getP4LatestRev(labelsyncName):
    if DEBUG > 4: print ("getLatestRev: labelsyncName = {}".format(labelsyncName))
    output = getP4RecommendedLabels(labelsyncName)
    if DEBUG > 4: print ("getLatestRev: output = {}".format(output))
    output = subprocess.check_output("p4 fstat {}  | grep headRev | cut -d ' ' -f 3".format(output.split('#')[0]), shell=True, universal_newlines=True)
    return output.strip()


def getP4LatestRecommendedLabel(labelsyncName):
    if DEBUG > 4: print ("getLatestRecommendedLabel: labelsyncName = {}".format(labelsyncName))
    a,b = getAndParseRecommendedLabel(labelsyncName).split('#')
    if DEBUG > 4: print ("getLatestRecommendedLabel: a = {} b = {}, returning b".format(a,b))
    return b


def getLastRunMiniReg(block):
    if DEBUG > 4: print ("getLastRunMiniReg: block = {}".format(block))
    return getLastRegRun(miniTable,block)
    #    output = subprocess.check_output("grep -i '^{BLK}' {FILE}".format(BLK=block,FILE=bookKeepMini), shell=True, universal_newlines=True)
    #    output = output.strip()
    #    a,b = output.split('=')
    #    return b


def getLastRunFullReg(block):
    if DEBUG > 4: print ("getLastRunFullReg: block = {}".format(block))
    return getLastRegRun(fullTable,block)
    #    output = subprocess.check_output("grep -i '^{BLK}' {FILE}".format(BLK=block,FILE=bookKeepFull), shell=True, universal_newlines=True)
    #    output = output.strip()
    #    a,b = output.split('=')
    #    return b


def getMiniLabelsBehindLatestRev(lastRunMiniReg,latestRev):
    if DEBUG > 4: print ("getMiniLabelsBehindLatestRev: lastRunMiniReg = {},latestRev = {}".format(lastRunMiniReg,latestRev))
    return getLabelsBehind(lastRunMiniReg,latestRev)


def getFullLabelsBehindLatestRev(lastRunFullReg,latestRev):
    if DEBUG > 4: print ("getFullLabelsBehindLatestRev: lastRunFullReg = {},latestRev = {}".format(lastRunFullReg,latestRev))
    return getLabelsBehind(lastRunFullReg,latestRev)


def getMiniDaysBehindLatestRev(labelsyncName,lastRunMiniReg,latestRev):
    if DEBUG > 4: print ("getMiniDaysBehindLatestRev: labelsyncName = {},lastRunMiniReg = {},latestRev = {}".format(labelsyncName,lastRunMiniReg,latestRev))
    return getDaysBehindLabel(labelsyncName,lastRunMiniReg,latestRev)


def getFullDaysBehindLatestRev(labelsyncName,lastRunFullReg,latestRev):
    if DEBUG > 4: print ("getFullDaysBehindLatestRev: labelsyncName = {},lastRunFullReg = {},latestRev = {}".format(labelsyncName,lastRunFullReg,latestRev))
    return getDaysBehindLabel(labelsyncName,lastRunFullReg,latestRev)


def getFullLabelsBehindRecommendedLabel(lastRunFullReg,latestRecommendedLabel):
    if DEBUG > 4: print ("getFullLabelsBehindRecommendedLabel: lastRunFullReg = {},latestRecommendedLabel = {}".format(lastRunFullReg,latestRecommendedLabel))
    return getLabelsBehind(lastRunFullReg,latestRecommendedLabel)


def getFullDaysBehindRecommendedLabel(labelsyncName,lastRunFullReg,latestRecommendedLabel):
    if DEBUG > 4: print ("getFullDaysBehindRecommendedLabel: labelsyncName = {},lastRunFullReg = {},latestRecommendedLabel = {}".format(
            labelsyncName,lastRunFullReg,latestRecommendedLabel))
    return getDaysBehindLabel(labelsyncName,lastRunFullReg,latestRecommendedLabel)


def getMiniLabelsBehindRecommendedLabel(lastRunMiniReg,latestRecommendedLabel):
    if DEBUG > 4: print ("getMiniLabelsBehindRecommendedLabel: lastRunMiniReg = {},latestRecommendedLabel = {}".format(lastRunMiniReg,latestRecommendedLabel))
    return getLabelsBehind(latestRecommendedLabel,lastRunMiniReg)


def getMiniDaysBehindRecommendedLabel(labelsyncName,lastRunMiniReg,latestRecommendedLabel):
    if DEBUG > 4: print ("getMiniDaysBehindRecommendedLabel: labelsyncName = {},lastRunMiniReg = {},latestRecommendedLabel = {}".format(
            labelsyncName,lastRunMiniReg,latestRecommendedLabel))
    return getDaysBehindLabel(labelsyncName,latestRecommendedLabel,lastRunMiniReg)


def getRecomendedLabelsBehindLastMiniRun(lastRunMiniReg,latestRecommendedLabel):
    if DEBUG > 4: print ("getRecomendedLabelsBehindLastMiniRun: lastRunMiniReg = {},latestRecommendedLabel = {}".format(lastRunMiniReg,latestRecommendedLabel))
    return getLabelsBehind(latestRecommendedLabel,lastRunMiniReg)##TODO: Note this is reversed order


def getRecomendedDaysBehindLastMiniRun(labelsyncName,lastRunMiniReg,latestRecommendedLabel):
    if DEBUG > 4: print ("getRecomendedDaysBehindLastMiniRun: labelsyncName = {},lastRunMiniReg = {},latestRecommendedLabel = {}".format(
            labelsyncName,lastRunMiniReg,latestRecommendedLabel))
    return getDaysBehindLabel(labelsyncName,latestRecommendedLabel,lastRunMiniReg)##TODO: Note this is reversed order



########################################################################
# Function Definitions: Helper Functions
########################################################################
def getLastRegRun(t,block):
    if DEBUG > 4: print ("getLastRegRun: t = {},block = {}".format(t,block))
    query = data[JNAME_SQL]['OrderedDistinctRegResults'].format(
        num=1,table=t,blk=block)
    returnedData = myUtils.getLastRegressionLabel(db,cursor,query)
    if DEBUG > 4: print ("getLastRegRun: table = {} data = {}".format(t,returnedData))
    if returnedData:
        returnedData = returnedData.split('#')[1]
        return returnedData
    else:
        return "0"

def getAndParseRecommendedLabel(labelsyncName):
    if DEBUG > 4: print ("getAndParseRecommendedLabel: labelsyncName = {}".format(labelsyncName))
    output = getP4RecommendedLabels(labelsyncName)
    if DEBUG > 4: print ("getAndParseRecommendedLabel: output = {}, returning {}".format(output,output.split(' - ')[0]))
    return output.split(' - ')[0]
    
def getDateFromP4Filelog(verifFilename,desiredLabelVersion):
    if DEBUG > 4: print ("getDateFromP4Filelog: verifFilename = {},desiredLabelVersion = {}".format(verifFilename,desiredLabelVersion))
    output = subprocess.check_output("p4 filelog {} | grep '^... #{}'".format(verifFilename,desiredLabelVersion), shell=True, universal_newlines=True)
    mystr = output.split(' ')[6] #I hope this position in the string doesn't change!!!!
    m = re.match(r"(\d{4})/(\d{2})/(\d{2})", mystr)
    if DEBUG > 4: print (m.groups())
    return datetime.strptime(' '.join(m.groups()), '%Y %m %d')

#TODO: converge with LabelX func
#def getDaysBehindLatestRev(labelsyncName,lastRunReg,latestRev):
#    if DEBUG > 4: print ("getDaysBehindLatestRev: labelsyncName = {},lastRunReg = {},latestRev = {}".format(labelsyncName,lastRunReg,latestRev))
#    try:
#        a,b = getAndParseRecommendedLabel(labelsyncName).split('#')
#        latestRevDate  = getDateFromP4Filelog(a,latestRev)
#        lastDLDate = getDateFromP4Filelog(a,lastRunReg)
#        delta = latestRevDate - lastDLDate
#        if DEBUG > 4: print ("getDaysBehindLatestRev: latestRevDate = {},lastDLDate = {},delta = {}".format(latestRevDate,lastDLDate,delta))
#        return delta.days
#    except:
#        if DEBUG > 4: print ("getDaysBehindLatestRev: Return '999'")
#        return "999"

def getDaysBehindLabel(labelsyncName,lastRunReg,labelX):
    if DEBUG > 4: print ("getDaysBehindLabel: labelsyncName = {},lastRunReg = {},latestRev = {}".format(labelsyncName,lastRunReg,labelX))
    try:
        a,b = getAndParseRecommendedLabel(labelsyncName).split('#')
        labelXDate  = getDateFromP4Filelog(a,labelX)
        lastDLDate = getDateFromP4Filelog(a,lastRunReg)
        delta = labelXDate - lastDLDate
        if DEBUG > 4: print ("getDaysBehindLabel: labelXDate = {},lastDLDate = {},delta = {}".format(labelXDate,lastDLDate,delta))
        return delta.days
    except:
        if DEBUG > 4: print ("getDaysBehindLabel: Return '999'")
        return "999"

def getP4RecommendedLabels(labelsyncName):
    if DEBUG > 4: print ("getRecommendedLabels: labelsyncName = {}".format(labelsyncName))
    outputLines = subprocess.check_output("p4 files {}".format(labelsyncName), shell=True, universal_newlines=True).split('\n')
    output = ""
    for i in outputLines:
        if "/{}/".format(DEPOT) in i:
            output = i.strip()
    assert(output),"Could not retrieve latest recommended label for depot "+DEPOT
    if DEBUG > 4: print ("getRecommendedLabels: output = {}".format(output))
    return output

def getLabelsBehind(a,b):
    if DEBUG > 4: print ("getLabelsBehind: a = {},b = {}".format(a,b))
    return str(int(b) - int(a))



