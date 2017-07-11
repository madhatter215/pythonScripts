#!/pkg/qct/software/python/3.5.2/bin/python

###############################################################################
# Filename: regressionBehindHtmlGenerator.py
# Author: cskebriti
# Description: 
#   .
###############################################################################
import sys                              # Std Lib: used here to print error message
import json                             # Std Lib: used to import email addr of blk owners
import pymssql                          # pip module: used for db connection and sql actions
import setup.config as config           # local app: top level config variables
import setup.sql_setup as sql_setup     # local app: keeps db passwd in separate file obfiscated
import helper.myfunc as myUtils         # local app: keep common functions there
#import trigger_consecutive_label_fail
import collections
import subprocess
import re
from datetime import datetime
import builtins

#Named Tuple Obj
Block = config.Block

DEBUG           = config.DEBUG
#DEBUG = 5 #override
NAPIER          = config.NAPIER
PROJ            = config.PROJ
dbTables        = config.dbTables
miniTable       = config.miniTable
fullTable       = config.fullTable

MINI_REG_BEHIND_THRESHOLD_MODERATE = config.MINI_REG_BEHIND_THRESHOLD_MODERATE
MINI_REG_BEHIND_THRESHOLD_SEVERE   = config.MINI_REG_BEHIND_THRESHOLD_SEVERE
FULL_REG_BEHIND_THRESHOLD_MODERATE = config.FULL_REG_BEHIND_THRESHOLD_MODERATE
FULL_REG_BEHIND_THRESHOLD_SEVERE   = config.FULL_REG_BEHIND_THRESHOLD_SEVERE
cellColors = ('one','b','c','d','red','yellow','green','grey')


##################################################################################################################################################################
##
    ################################
    ## TOP: Header of HTML for Email
TOP = '''\
<style type="text/css">
  .one    {{ border-collapse:collapse;table-layout:fixed;COLOR: black; width: 1500px;word-wrap: break-word;}}
  .b      {{ border-style:solid; border-width:3px;border-color:#333333;padding:10px;width:10px; text-align:center;COLOR: black;}}
  .c      {{ border-style:solid; border-width:3px;border-color:#333333;text-align: left;padding:10px;background-color:#99ccff;width:10px;COLOR: black;}}
  .d      {{ border-style:solid; border-width:3px;border-color:#333333;text-align: left;padding:10px;background-color:#79d379;width:10px;COLOR: black;}}
  .red    {{ border-style:solid; border-width:3px;border-color:#333333;text-align: center; padding:10px;background-color:#ff704d;width:10px;COLOR: black;}}
  .yellow {{ border-style:solid; border-width:3px;border-color:#333333;text-align: center;padding:10px;background-color:#ffff80;width:10px;COLOR: black;}}
  .green  {{ border-style:solid; border-width:3px;border-color:#333333;text-align: center;padding:10px;background-color:#66ff66;width:10px;COLOR: black;}}
  .grey   {{ border-style:solid; border-width:3px;border-color:#333333;text-align: center;padding:10px;background-color:#e0e0d1;width:10px;COLOR: black;}}
</style>
<H3>Regression Verif Design Label Summary Table: {timeNow} </H3>
<table class="one">
  <tr>
    <th class="c">Block</th>
    <th class="c">HeadRev</th>
    <th class="c">Last Mini Regression Run</th>
    <th class="c">Recommended Label</th>
    <th class="c">Last Full Regression Run</th>

    <th class="c">MINI: Reg Behind HeadRev</th>

    <th class="c">Recommended Label: Behind Last Mini Reg</th>
    <th class="c">FULL: Reg Behind Recommended Label</th>

  </tr>
'''.format(timeNow=datetime.now().strftime('%Y-%m-%d %H:%M'))
#############    <th class="c">FULL: Reg Behind HeadRev</th>


    ###########
    ## MIDDLE
MIDDLE = '''\
  <tr>
    <th class="d">{blockname}</th>
    <td class="d">VERIF#{latestRev}</td>
    
    <td class="{colorLastRunMiniReg}">VERIF#{lastRunMiniReg}</td>
    <td class="{colorLatestRecommendedLabel}">VERIF#{latestRecommendedLabel}</td>
    <td class="{colorLastRunFullReg}">VERIF#{lastRunFullReg}</td>

    <td class="{colorMiniBehindLatestRev}">{miniBehindLatestRev}</td>
    
    <td class="{colorMiniBehindRecommended}">{miniBehindRecommended}</td>
    <td class="{colorFullBehindRecommended}">{fullBehindRecommended}</td>
  </tr>
'''
#############    <td class="{colorFullBehindLatestRev}">{fullBehindLatestRev}</td>



    ##################################################
    ## BOTTOM: Static, just closes the HTML table
BOTTOM = '''\
</table>
<br/>'''
#############

##
##################################################################################################################################################################


########################################################################
# Function Definitions:
########################################################################
def createHTML(myRecords):
    if DEBUG: print ("\n\tInside function 'createHTML' of ", __name__)

    #import pdb; pdb.set_trace()


    ##########################################
    #Work the middle to add rows to the table
    middle = ""
    if (isinstance(myRecords, Block)):
        middle = createHtmlMiddle(myRecords)
    elif (isinstance(myRecords, builtins.list)):
        for i in myRecords:
            middle += createHtmlMiddle(i)
    #
    if DEBUG > 4: print (middle)
    return (TOP+middle+BOTTOM)


##########################
def createHtmlMiddle(i):
    return MIDDLE.format(

        colorLastRunMiniReg = \
            determineCellColorMini(min(int(i.miniLabelsBehindLatestRev),int(i.miniDaysBehindLatestRev))),

        colorLatestRecommendedLabel = \
            determineCellColorMini(min(int(i.recomendedLabelsBehindLastMiniRun),int(i.recomendedDaysBehindLastMiniRun))),

        colorLastRunFullReg = \
            determineCellColorFull(min(int(i.fullLabelsBehindRecommendedLabel),int(i.fullDaysBehindRecommendedLabel))),

        colorMiniBehindLatestRev = \
            determineCellColorMini(min(int(i.miniLabelsBehindLatestRev),int(i.miniDaysBehindLatestRev))),

#        colorFullBehindLatestRev = \
#            determineCellColorFull(min(int(i.fullLabelsBehindLatestRev),int(i.fullDaysBehindLatestRev))),

        colorMiniBehindRecommended = \
            determineCellColorMini(min(int(i.recomendedLabelsBehindLastMiniRun),int(i.recomendedDaysBehindLastMiniRun))),

        colorFullBehindRecommended = \
            determineCellColorFull(min(int(i.fullLabelsBehindRecommendedLabel),int(i.fullDaysBehindRecommendedLabel))),


        blockname                       = i.blockname,
        latestRev                       = i.latestRev,
        latestRecommendedLabel          = i.latestRecommendedLabel,
        lastRunMiniReg                  = i.lastRunMiniReg,
        lastRunFullReg                  = i.lastRunFullReg,

        miniBehindLatestRev       = "{} labels / {} days".format(i.miniLabelsBehindLatestRev, i.miniDaysBehindLatestRev),
        fullBehindLatestRev       = "{} labels / {} days".format(i.fullLabelsBehindLatestRev,i.fullDaysBehindLatestRev),

        miniBehindRecommended     = "{} labels / {} days".format(i.miniLabelsBehindRecommendedLabel,i.miniDaysBehindRecommendedLabel),
        fullBehindRecommended     = "{} labels / {} days".format(i.fullLabelsBehindRecommendedLabel,i.fullDaysBehindRecommendedLabel) )


########################################################################
# Function Definitions: Helper Functions
########################################################################
'''
If the mini is behind by 2 days, we can mark it as yellow for columns “Num of days mini is behind” and “Num of labels mini is behind”
If the mini is behind by 3 days, we can mark it as red.

If the full is behind by 4 days, we can mark it as yellow for columns “Num of days full is behind” and “Num of labels full is behind”
If the full is behind by 7 days, we can mark it as red.
'''

def determineCellColorMini(numBehind):
    return determineCellColor(numBehind, 
        MINI_REG_BEHIND_THRESHOLD_MODERATE, 
        MINI_REG_BEHIND_THRESHOLD_SEVERE)

def determineCellColorFull(numBehind):
    return determineCellColor(numBehind, 
        FULL_REG_BEHIND_THRESHOLD_MODERATE, 
        FULL_REG_BEHIND_THRESHOLD_SEVERE)

def determineCellColor(numBehind,moderate,severe):
    try:
        myNumberBehind = int(numBehind)
        if myNumberBehind < moderate: return 'green'
        elif myNumberBehind < severe: return 'yellow'
        elif myNumberBehind >= severe: return 'red'
        else: return 'grey'
    except:
        return 'grey'


