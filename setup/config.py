#!/pkg/qct/software/python/3.5.2/bin/python

###############################################################################
# Typical config.py with global configuration objects and settings
###############################################################################
import sys, os, getopt
from pathlib import Path
import collections
import json


#############################################
## Setup path to find packages for imports ##
if '/prj/helium_tools/python/lib/python3.5/site-packages' not in sys.path:
    sys.path.append('/prj/helium_tools/python/lib/python3.5/site-packages')
if '/pkg/qct/software/python/3.5.2' not in sys.path:
    sys.path.append('/prj/helium_tools/python/lib/python3.5/site-packages')
## Append python script root to path to allow other scripts to perform local
# imports  Line below assumes this file is located one directory below root
sys.path.append(str(Path(os.path.dirname(os.path.realpath(__file__))).parent))



#############################################
##          Global project config          ##
#############################################
DEBUG                   = 3  #default, this gets set below
NAPIER                  = -1 #default, this gets set below
#SCRIPT_ROOT            = '/usr2/c_ckebri/pythonScripts' 
ScriptPathObj           = Path(os.path.dirname(os.path.realpath(__file__))).parent
LithiumScriptsPathObj   = Path('/prj/helium_tools/lithium/scripts')
myJsonFile              = ScriptPathObj / 'input' / 'JsonObjCollection.json'

assert(ScriptPathObj.exists()),"Error: Path '{}' does not exist".format(ScriptPathObj)
assert(myJsonFile.is_file()),"Error: File '{}' does not exist".format(myJsonFile)





##################################################
## Get command line options and set global vars ##
detectProj  = ''
PROJECT     = ''
EMAIL_FLAG  = False
BLOCK       = ''    #used in AutoCreateLabels
P4CLIENT    = ''    #used in AutoCreateLabels
NOCLEAN     = False #used in AutoCreateLabels
P4LABEL     = ''    #used in AutoCreateLabels
def usage():
    print ("\nUsage: {} --project [hawkeye|napier|napier1p0]\n".format(sys.argv[0]))

try: #Get command line args
    optlist,args = getopt.getopt(sys.argv[1:],"hdbl:",["help","project=","debug=","mail","block=","p4client=","no-clean","p4label="])
    for a,b in optlist:
        if a in ('-h', '--help'):
            usage()
            sys.exit()
        elif a in ('-d', '--debug'):
            print ("DEBUG Override:\n DEBUG='{}'".format(b))
            DEBUG = int(b)
        elif a in ('-p', '--project'):
            detectProj = b
        elif a in ('--mail'):
            EMAIL_FLAG = True
        elif a in ('-b', '--block'):
            BLOCK = b.lower()
        elif a in ('--p4client'):
            P4CLIENT = b
        elif a in ('--no-clean','--no-cleanup'):
            NOCLEAN = True
        elif a in ('-l','--p4label'):
            P4LABEL = b
        else:
            assert(False), usage()
        ###

    ###
    # detect and set project here
    if (detectProj.lower() == "napier"):
        NAPIER = 1
        PROJECT = 'NAPIER' #Json Key

    elif (detectProj.lower() == "hawkeye"):
        NAPIER = 0
        PROJECT = 'HAWKEYE' #Json Key

    elif (detectProj.lower() == "napier1p0"):
        NAPIER = 1
        PROJECT = 'NAPIERV1' #Json Key
        


    else:
        raise SystemExit(usage())




except getopt.GetoptError as e:
    print (e)
    usage()
    sys.exit(2)

######################################
#Set's a string variable if Napier
# perform some double checking
######################################
if NAPIER == -1: raise SystemExit
if PROJECT == "": raise SystemExit("No project detected")

print ("DEBUG='{}'".format(repr(DEBUG)))
print ("NAPIER='{}'\n\n".format(repr(NAPIER)))
PROJ    = '_NAPIER' if NAPIER else ''


######################################
# Get Json Data
with myJsonFile.open() as data_file:
    myJsonData = json.load(data_file)
    data_file.close()

tempJsonProjData = myJsonData['Projects']['Lithium'][PROJECT]
############
#######
####
##





####################################################################################################################################
miniTable   = tempJsonProjData['DBTables']['MINI'] #string
fullTable   = tempJsonProjData['DBTables']['FULL'] #string
dbTables    = (miniTable,fullTable) #tuple

DEPOT                               = tempJsonProjData['DEPOT']
PRJ_BRANCH                          = tempJsonProjData['PRJ_BRANCH']
projectName                         = tempJsonProjData['projectName']

lithiumRegBookKeepingFileFull       = ScriptPathObj / tempJsonProjData['BL_INFO_FILE_FULL']
lithiumRegParamInputFileFull        = ScriptPathObj / tempJsonProjData['P4_REG_INPUT_FILE_FULL']
lithiumRegBookKeepingFileMini       = ScriptPathObj / tempJsonProjData['BL_INFO_FILE_MINI']
lithiumRegParamInputFileMini        = ScriptPathObj / tempJsonProjData['P4_REG_INPUT_FILE_MINI']



##########################################
## test5.py/verifLabelRegressionDiff.py ##
VerifDiffLabelHtmlOutputFile  = LithiumScriptsPathObj / 'output' / projectName / tempJsonProjData['VerifLabelRegDiffHtmlFilename']
VerifDiffLabelHtmlFileDBTable = tempJsonProjData['VerifLabelDiffDBTable']

#Named Tuple
Block = collections.namedtuple('Block', \
'blockname \
latestRev \
latestRecommendedLabel \
lastRunMiniReg \
lastRunFullReg \
recomendedLabelsBehindLastMiniRun \
recomendedDaysBehindLastMiniRun \
miniLabelsBehindLatestRev \
fullLabelsBehindLatestRev \
miniDaysBehindLatestRev \
fullDaysBehindLatestRev \
miniLabelsBehindRecommendedLabel \
fullLabelsBehindRecommendedLabel \
miniDaysBehindRecommendedLabel \
fullDaysBehindRecommendedLabel')


##########################################
## test6.py
DesignToVerifDiffLabelHtmlOutputFile    = LithiumScriptsPathObj / 'output' / projectName / tempJsonProjData['DesignToVerifLabelDiffHtmlFile']
DesignToVerifDiffLabelHtmlOutputDBTable = tempJsonProjData['DesignToVerifLabelDiffDBTable']



##########################################
## emailBlockOwner.py                   ##
emailSenderOrigin = "RegressionAutomation@DoNotReply.com"
emailOnlyMe       = "c_ckebri@qti.qualcomm.com"
emailCarbonCopy   = "manager@qti.qualcomm.com, c_ckebri@qti.qualcomm.com"




#trigger vars
CONSECUTIVE_FAIL_TRIGGER    = 3##test3.py
LASTXDAYS_TRIGGER           = 14
#regressionBehindHtmlGenerator
MINI_REG_BEHIND_THRESHOLD_MODERATE = 2
MINI_REG_BEHIND_THRESHOLD_SEVERE   = 3
FULL_REG_BEHIND_THRESHOLD_MODERATE = 4
FULL_REG_BEHIND_THRESHOLD_SEVERE   = 7



def setDB(a,b):
    global top_db,top_cursor
    top_db      = a
    top_cursor  = b

def getDB():
    global top_db,top_cursor
    return (top_db,top_cursor)



