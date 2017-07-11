#!/pkg/qct/software/python/3.5.2/bin/python

###############################################################################
# Filename: verifLabelRegressionDiff.py
# Author: cskebriti
# Description: 
#   Creates HTML for diffRegVerifLabel to be displayed on http://napier_mac/
#   It stores the file on disk and performs an SQL INSERT into the HeliumDB
###############################################################################
import sys, os                          # Std Lib: used here to print error message
import setup.config as config           # local app: top level config variables
import json                             # Std Lib: used to import email addr of blk owners
import pymssql                          # pip module: used for db connection and sql actions
import setup.sql_setup as sql_setup     # local app: keeps db passwd in separate file obfiscated
import helper.myfunc as myUtils         # local app: keep common functions there
#import trigger_consecutive_label_fail
#import emailBlockOwner                 # local app: called with list of block names
import collections, operator
import subprocess
import re
from datetime import datetime
import helper.regressionBehindHtmlGenerator \
        as regressionBehindHtmlGenerator

import helper.regressionBehindEmailer as regressionBehindEmailer

DEBUG           = config.DEBUG
#DEBUG           = 3 #Override
NAPIER          = config.NAPIER
PROJ            = config.PROJ
data            = config.myJsonData

miniTable       = config.miniTable#string
fullTable       = config.fullTable#string
dbTables        = config.dbTables #tuple

DEPOT           = config.DEPOT
PRJ_BRANCH      = config.PRJ_BRANCH
projectName     = config.projectName

bookKeepFull    = config.lithiumRegBookKeepingFileMini
bookKeepMini    = config.lithiumRegBookKeepingFileFull

inputParamFileFull  = config.lithiumRegParamInputFileFull
inputParamFileMini  = config.lithiumRegParamInputFileMini

#Named Tuple Obj
Block = config.Block

EMAIL_FLAG      = config.EMAIL_FLAG

#######################Json Keys######################################
#JNAME_P4           = 'P4FilesCollection'
JNAME_SQL          = 'SqlQueryCollection'
#BlockNameQuery  = 'NapierBlocks' if NAPIER else 'HawkeyeBlocks'
JNAME_P4        = 'P4Labels_NAPIER' if NAPIER else 'P4Labels_HAWKEYE'
######################################################################

#Output file for HTML, type=pathlib.PosixPath
HtmlOutputFile  = config.VerifDiffLabelHtmlOutputFile
diffRegTable    = config.VerifDiffLabelHtmlFileDBTable


if not (HtmlOutputFile and diffRegTable):
    print ("No HTML output file specified or HeliumDB table to put the Html file into!")
    raise SystemExit


########################################################################
########################################################################
########################################################################
########################################################################
########################################################################
#       Main: Start of Program                                         #
########################################################################
########################################################################
if 'main' in __name__: print ("Start of Program")


os.environ['PATH'] += os.pathsep + '/pkg/qct/software/p4'
os.putenv('P4PORT', "p2.qca.qualcomm.com:1666")


# Create db connection
db,cursor = sql_setup.opendb()
config.setDB(db,cursor)
from helper.p4_functions import *


# Create global list to store tuples
myRecords = list()


try:
    for i in data[JNAME_P4]:#['XP4Labels_NAPIER']:
        
        print ("\n\tBlock {}".format(i))
        if DEBUG: print ("Using '{}' for labelname \n and '{}' for VERIF filename".format(
            data[JNAME_P4][i], getAndParseRecommendedLabel(data[JNAME_P4][i]).split('#')[0]))
        ##
        labelsyncName = data[JNAME_P4][i]
        #####################################################################################
        #
        ####
        blockname                       = i
        #
        latestRev                       = \
            getP4LatestRev(labelsyncName)
        #
        latestRecommendedLabel          = \
            getP4LatestRecommendedLabel(labelsyncName)
        #
        lastRunMiniReg                  = \
            getLastRunMiniReg(blockname)
        #
        lastRunFullReg                  = \
            getLastRunFullReg(blockname)
        #
        recomendedLabelsBehindLastMiniRun       = \
            getRecomendedLabelsBehindLastMiniRun(lastRunMiniReg,latestRecommendedLabel)
        #
        recomendedDaysBehindLastMiniRun       = \
            getRecomendedDaysBehindLastMiniRun(labelsyncName,lastRunFullReg,latestRecommendedLabel)
        #
        miniLabelsBehindLatestRev       = \
            getMiniLabelsBehindLatestRev(lastRunMiniReg,latestRev)
        #
        fullLabelsBehindLatestRev       = \
            getFullLabelsBehindLatestRev(lastRunFullReg,latestRev)
        #
        miniDaysBehindLatestRev         = \
            getMiniDaysBehindLatestRev(labelsyncName,lastRunMiniReg,latestRev)
        #
        fullDaysBehindLatestRev         = \
            getFullDaysBehindLatestRev(labelsyncName,lastRunFullReg,latestRev)
        #
        miniLabelsBehindRecommendedLabel         = \
            getMiniLabelsBehindRecommendedLabel(lastRunMiniReg,latestRecommendedLabel)
        #
        fullLabelsBehindRecommendedLabel         = \
            getFullLabelsBehindRecommendedLabel(lastRunFullReg,latestRecommendedLabel)
        #
        miniDaysBehindRecommendedLabel         = \
            getMiniDaysBehindRecommendedLabel(labelsyncName,lastRunMiniReg,latestRecommendedLabel)
        #
        fullDaysBehindRecommendedLabel         = \
            getFullDaysBehindRecommendedLabel(labelsyncName,lastRunFullReg,latestRecommendedLabel)
        #
        #
        #####################################################################################
        # Create the tuple and append to the list
        ##############################################################
        newBlock = Block(
                blockname                       = blockname, 
                latestRev                       = latestRev,
                latestRecommendedLabel          = latestRecommendedLabel, 
                lastRunMiniReg                  = lastRunMiniReg, 
                lastRunFullReg                  = lastRunFullReg, 

                recomendedLabelsBehindLastMiniRun = recomendedLabelsBehindLastMiniRun,
                recomendedDaysBehindLastMiniRun   = recomendedLabelsBehindLastMiniRun,

                miniLabelsBehindLatestRev       = miniLabelsBehindLatestRev, 
                fullLabelsBehindLatestRev       = fullLabelsBehindLatestRev,
                miniDaysBehindLatestRev         = miniDaysBehindLatestRev,
                fullDaysBehindLatestRev         = fullDaysBehindLatestRev,

                miniLabelsBehindRecommendedLabel= miniLabelsBehindRecommendedLabel,
                fullLabelsBehindRecommendedLabel= fullLabelsBehindRecommendedLabel,
                miniDaysBehindRecommendedLabel  = miniDaysBehindRecommendedLabel,
                fullDaysBehindRecommendedLabel  = fullDaysBehindRecommendedLabel )
        ##############################################################
        myRecords.append(newBlock)
        ####



    ####
    # Print a summary, sort myRecords, and print the generated Html output
    ####
    print ("\n{}\n{}".format("My Records Summary:".center(62),"="*62))
    for i in myRecords:
        msg = "{:30} {:3} {:3} {:3} {:3} {:3} {:3} {:3} {:3} {:3} {:3}"
        print (msg.format(
                i.blockname,
                i.latestRev,
                i.latestRecommendedLabel,
                i.lastRunMiniReg,
                i.lastRunFullReg,
                i.miniLabelsBehindLatestRev,
                i.fullLabelsBehindLatestRev,
                i.miniDaysBehindLatestRev,
                i.fullDaysBehindLatestRev,
                i.fullLabelsBehindRecommendedLabel,
                i.fullDaysBehindRecommendedLabel))
    print ("blockname latestRev latestRecommendedLabel lastRunMiniReg lastRunFullReg \
miniLabelsBehindLatestRev fullLabelsBehindLatestRev miniDaysBehindLatestRev fullDaysBehindLatestRev\
fullLabelsBehindRecommendedLabel fullDaysBehindRecommendedLabel\n\n")

    myRecords = sorted(myRecords, key=operator.attrgetter('blockname'))

    #######################################################################
    ## Run the automation script for sending email notifications
    if EMAIL_FLAG: regressionBehindEmailer.dispatchEmails(myRecords)
    #######################################################################

    
    #####################################################################################################
    # Now let's save the Html file as text and stuff the it into the Helium DB for the dashboard
    #####################################################################################################
    myHtmlAsText = regressionBehindHtmlGenerator.createHTML(myRecords)
    #
    ##Save to file
    print ("\nSave to file '{}'".format(HtmlOutputFile))
    HtmlOutputFile.write_text(myHtmlAsText)
    #
    ##Make sure no single quotes are used in the Html text, use only double quotes. Check and replace any
    # single quotest as an extra precaution before we execute the sql statement
    myHtmlAsText.replace("'", '"')
    #
    ##
    print ("Insert into table '{}'".format(diffRegTable))
    if DEBUG < 3:
      sql = \
      """
      IF NOT EXISTS (SELECT * FROM [dbo].[{1}]
                     WHERE HTMLfile = '{0}')
      INSERT INTO {1} (HTMLfile) values('{0}')
      """
      cursor.execute(sql.format(myHtmlAsText,diffRegTable))
      db.commit()



####
# No matter what exception occurs, close the DB connection
####
finally: # Disconnect from server 
    print ("\n\n**Closing DB connection**\n")
    sql_setup.closedb(db,cursor)

