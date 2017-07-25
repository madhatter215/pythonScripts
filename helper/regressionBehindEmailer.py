#!/pkg/qct/software/python/3.6.0/bin/python

###############################################################################
# Filename: ??.py
# Author: cskebriti
# Description: 
#   .
###############################################################################
#import sys                              # Std Lib: used here to print error message
import json                             # Std Lib: used to import email addr of blk owners
import setup.config as config           # local app: top level config variables
import helper.myfunc as myUtils         # local app: keep common functions there
import collections
from helper.regressionBehindHtmlGenerator import *
import helper.myfunc as myUtils         # local app: keep common functions there

#Json handle
JsonObj = config.myJsonData

#Named Tuple Obj
Block = config.Block

#Email address of automation engineer
emailOnlyMe = config.emailOnlyMe
emailCarbonCopy = config.emailCarbonCopy

projAlias = config.projectName if (config.projectName != 'napier') else 'Napier AX' #Nickname for napier on main branch


################################################################
# Function Definitions: 
################################################################

############
def dispatchEmails(records):
    if DEBUG: print ("\n\tInside function 'dispatchEmails' of ", __name__)
    for i in records:
        processBlock(i)


############
def dispatchEmailSummary(records):
    #lithium.dv.mac.leads
    if DEBUG: print ("\n\tInside function 'dispatchEmailSummary' of ", __name__)
    for i in records:
        processBlock(i)


############
def processBlock(i):
    if DEBUG: print ("\n\tInside function 'processBlock' of ", __name__)

    if (determineCellColorMini(min(int(i.miniLabelsBehindLatestRev),int(i.miniDaysBehindLatestRev)))                     == 'red' or 
        determineCellColorMini(min(int(i.recomendedLabelsBehindLastMiniRun),int(i.recomendedDaysBehindLastMiniRun)))     == 'red'):
        
        print ("\nprocessBlock Mini Check:", i.blockname, "failed check, pls check MINI cron")
        print ("processBlock Mini Check:", "latest HeadRev = {}\tlast mini reg = {}\n\n".format(i.latestRev, i.lastRunMiniReg))
        #
        createAndSendEmailMini(i)
        ####


    elif (
        determineCellColorFull(min(int(i.fullLabelsBehindRecommendedLabel),int(i.fullDaysBehindRecommendedLabel)))  == 'red' or
        determineCellColorFull(min(int(i.fullLabelsBehindRecommendedLabel),int(i.fullDaysBehindRecommendedLabel)))  == 'red'):
        
        print ("\nprocessBlock Full Check:", i.blockname, "failed check, pls check FULL cron")
        print ("processBlock Full Check:", "recommended label = {}\tlast full reg = {}\n\n".format(i.latestRecommendedLabel, i.lastRunFullReg))
        #
        createAndSendEmailFull(i)
        ####


############
def createAndSendEmailMini(x):
    if DEBUG: print ("\n\tInside function 'createAndSendEmailMini' of ", __name__)
    subject = "{projName}: {blk} - Regression Behind, Check MINI Cron".format(projName=projAlias, blk=x.blockname)
    createAndSendEmail(x, subject)


def createAndSendEmailFull(x):
    if DEBUG: print ("\n\tInside function 'createAndSendEmailFull' of ", __name__)
    subject = "{projName}: {blk} - Regression Behind, Check FULL Cron".format(projName=projAlias, blk=x.blockname)
    createAndSendEmail(x, subject)


def createAndSendEmail(y, msgSubj):
    if DEBUG: print ("\n\tInside function 'createAndSendEmail' of ", __name__)
    MsgHTML = createHTML(y)
    blk_email_key = y.blockname.upper().split('_')[0]#Remove napier from block name to index json key
    try:
        recips = JsonObj['BlockOwnersEmailAddr'][blk_email_key]
        recips = recips.replace(';',',')#Using semicolon so I can copy/paste to outlook email, convienence
        recips += ", " + emailCarbonCopy
        recips = recips.split(', ')
    except KeyError as e:
        print ("Error:",e)
        recips = [emailOnlyMe]
    ##
    #if DEBUG > 2: 
    print ("recips = {}\tmsgSubj = {}".format(recips, msgSubj))
    #
    #################
    ## Send Message:
    #################
    #
    if DEBUG < 2: 
        myUtils.sendEmail(recips, msgSubj, MsgHTML)
    #
    ####


