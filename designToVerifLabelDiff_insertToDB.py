#!/pkg/qct/software/python/3.5.2/bin/python

###############################################################################
# Filename: test6.py
# Author: cskebriti                                                           #
# Description:                                                                #
#                                                                             #
#                                                                             #
#   This program picks up the HTML file generated by                          #
#     'versiondiff_hawkeye_napier.pl' and stuffs it into the HeliumDB         #
#     table based on project (e.g. "LithiumNapier_DesignToVerif_LabelDiff"    #
#     for napier).                                                            #
#                                                                             #
#   The Html file is processed only if the timestamp is recent (<1day).       #
#                                                                             #
# See http://napier_mac/diffDesignToLabel.aspx                                #
#                                                                             #
###############################################################################
import sys, os                                  # Std Lib: used here to print error message
import setup.config as config                   # local app: top level config variables
from datetime import datetime, timedelta        # Std Lib: used to compute age of html file
from pathlib import Path                        # Std Lib: to get to json file
import setup.sql_setup as sql_setup             # local app: keeps db passwd in separate file obfiscated



############################################
## Get global config objects and settings ##
DEBUG           = config.DEBUG
HtmlFile        = config.DesignToVerifDiffLabelHtmlOutputFile   #'Path' object
dbTable         = config.DesignToVerifDiffLabelHtmlOutputDBTable#type string
print ("Html file to read in:\n  '{}'".format(str(HtmlFile)))
print ("Helium DB table to insert to:\n  '{}'".format(dbTable))


################################
## Check that the file exists ##
assert(HtmlFile.exists()),  "Error: Path '{}' does not exist".format(HtmlFile)
assert(HtmlFile.is_file()), "Error: File '{}' does not exist".format(HtmlFile)

HtmlFileAsText = HtmlFile.read_text()
HtmlFileAsText.replace("'", '"') #No single quotes, use only double quotes


######################
## Global Constants ##
ONE_DAY_OLD = datetime.now() - timedelta(days=1)



########################################################################
# Function Definitions:
########################################################################

def insertToDB(HtmlFile):
    ######################
    # Create db connection
    db,cursor = sql_setup.opendb()
    try:
        sql = \
        """
        IF NOT EXISTS (SELECT * FROM [dbo].[{1}]
                       WHERE HTMLfile = '{0}')
        INSERT INTO {1} (HTMLfile) VALUES ('{0}')
        """
        print (sql)
#        import pdb; pdb.set_trace()
        cursor.execute(sql.format(HtmlFileAsText,dbTable))
        if DEBUG:
            print ("Debug option set, execute INSERT to DB but will not commit!")
        else:
            db.commit()
        return (cursor.rowcount)
    ####
    # No matter what exception occurs, close the DB connection
    finally: # Disconnect from server 
        print ("\n\n**Closing DB connection**\n")
        sql_setup.closedb(db,cursor)






########################################################################
# Main: Start of Program                                              ##
########################################################################
if 'main' in __name__: print ("\n\n****Start of Program****")

lastModified = datetime.fromtimestamp(HtmlFile.stat().st_mtime)
t = lastModified - timedelta(days=1)
#print ("lastModified = '{}', t = '{}', ONE_DAY_OLD = '{}'".format(lastModified,t,ONE_DAY_OLD))

if t < ONE_DAY_OLD:
    print ("Fresh!")
    if insertToDB(HtmlFile): print ("InsertToDB: Success")
    else: print ("InsertToDB: Already up-to-date")

else:
    print ("File found is not recent, exiting program")


