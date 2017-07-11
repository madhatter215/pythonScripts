#!/pkg/qct/software/python/3.5.2/bin/python

###############################################################################
# Filename: consecutiveRegFailEmailer.py
# Author: cskebriti
# Description: 
#   Detects consecutive regression failures (i.e. three consecutive verif 
#     labels fail) and dispatches email notification to block owners. 
###############################################################################
import sys, os                              # Std Lib: used here to print error message
import setup.config as config               # local app: top level config variables
import json                                 # Std Lib: used to import email addr of blk owners
import pymssql                              # pip module: used for db connection and sql actions
import setup.sql_setup as sql_setup         # local app: keeps db passwd in separate file obfiscated
import helper.myfunc as myUtils             # local app: keep common functions there
#import trigger_consecutive_label_fail
import helper.emailBlockOwner \
        as emailBlockOwner                  # local app: called with list of block names


DEBUG           = config.DEBUG
#DEBUG = 3 #override
NAPIER          = config.NAPIER
miniTable       = config.miniTable
fullTable       = config.fullTable
dbTables        = config.dbTables #mini/full
CONSECUTIVE_FAIL_TRIGGER = \
  config.CONSECUTIVE_FAIL_TRIGGER

assert(miniTable),"Error: No config object found"
assert(fullTable),"Error: No config object found"
assert(dbTables),"Error: No config object found"
assert(CONSECUTIVE_FAIL_TRIGGER),"Error: No config object found"


###########################################
##         Json Data and Keys            ##
data            = config.myJsonData
JNAME           = 'SqlQueryCollection'
BlockNameQuery  = 'NapierBlocks' if NAPIER else 'HawkeyeBlocks'
q               = 'ConsecutiveLabelFails'





########################################################################
# Main: Start of Program                                               #
########################################################################
if 'main' in __name__: print ("\n\n*****Start of Program*****")


# Create db connection
db,cursor = sql_setup.opendb()

# Initialize global variable to keep blocks that have consecutive fails
failedBlocks = list()

try:

  for t in dbTables:
      print ("\nSTART in table '{}'".format(t))
#            t = dbTables[0]
#      t = dbTables[0]
#      print ("\n\nSTART in table '{}'".format(t))

      getBlocksQuery = data[JNAME][BlockNameQuery].format(table=t)
      for block in myUtils.getBlocks2(db,cursor, getBlocksQuery):

            print ("\n\tInfo: Checking block {} in table {}".format(block, t))
            #######################################################
            # Initialize the value, starting check for a new block
            rowFetchResultCnt       = 0       #Keep track num of rows returned
            curBlockFailCount       = 0
#            distinctReg             = 0       #Keep track num distinct reg
            myResults               = list()
            distinctNumOfLabels     = set() #Use set to prevent dupicate label version numbers
            ################################################
            #
            query = data[JNAME]['OrderedDistinctRegResults2'].format(
                num=CONSECUTIVE_FAIL_TRIGGER,table=t,blk=block)
            if DEBUG > 4: print (query)
            
            #####################
            # Execute sql query #
            cursor.execute(query)
            
            ################################################
            ## Inner Loop to check results for current block
            # Fetch first row from results
            row = cursor.fetchone()
            while row:
                rowFetchResultCnt += 1
                if DEBUG: print (row)
                block,regName,regResults,regTotalTC,regPassRate,regDate = row
                myRecord = block,regName,regResults,regTotalTC,regPassRate,regDate
                myResults.append(myRecord)
                if DEBUG > 3: print ("\tregName={},regResults={},regTotalTC={},regPassRate={},regDate={}".format(
                                    regName,regResults,regTotalTC,regPassRate,regDate))
                if "PASS" not in regResults.upper(): # ~pass -> failed
                    curBlockFailCount += 1
                try: distinctNumOfLabels.add(regName.split('#')[1])
                except: pass #do nothing
                row = cursor.fetchone()
            ############
            # Evaluate 
            if (len(distinctNumOfLabels) >= CONSECUTIVE_FAIL_TRIGGER) and (rowFetchResultCnt - curBlockFailCount == 0):
                print ("They all failed for block ",block)
                myTup = t,block,myResults
                failedBlocks.append(myTup)
            else: continue #dont process the current block, move on to the next

                
except Exception as e:
    print (e)
#    print ("\n\nUnexpected error:", sys.exc_info()[0], "\n")

finally: # Disconnect from server 
    print ("\n\n**Closing DB connection**\n")
    sql_setup.closedb(db,cursor)




######################################
##Process failing blocks
if failedBlocks:
    msg = "\nFailed Block Summary:\n"
    for b in failedBlocks:
        t,x,y = b
        msg += "\tTrigger email for block '{}' in table '{}'\n".format(x,t)
    print (msg,"\n")
    emailBlockOwner.dispatchEmails(failedBlocks)


print ("\n\nSummary of Checks:\n\tRan consecutive regression failure checks for '{prj}' in '{tb}' tables\n".format(
        prj=BlockNameQuery,tb=', '.join(dbTables)))




