#!/pkg/qct/software/python/3.5.2/bin/python

###############################################################################
import json                         # Std Lib: used to import email addr of blk owners
import setup.config as config       # local app: top level config variables


DEBUG           = config.DEBUG
#DEBUG = 1 #Override
myJsonFile      = config.myJsonFile
#JNAME           = 'SqlQueryCollection'
#q               = 'ConsecutiveLabelFails'

import smtplib                  # Std Lib: email server
from email.mime.multipart \
        import MIMEMultipart    # Std Lib: email msg
from email.mime.text \
        import MIMEText         # Std Lib: email msg



def sendEmail(msgRecipientList, msgSubject, msgBodyHtml, msgSender = config.emailSenderOrigin):
    if DEBUG: print ("\n\tInside function 'sendEmail' of ", __name__)
    #import pdb; pdb.set_trace()
    ##
    recipients = msgRecipientList \
        if not DEBUG else [config.emailOnlyMe]

    # Create message container - the correct MIME type is multipart/alternative.
    msg = MIMEMultipart('alternative')
    msg['Subject']  = msgSubject
    msg['From']     = msgSender
    msg['To']       = ', '.join(recipients) #type string

    # Generate Html Message
    messageBody = msgBodyHtml

    text = ""
    html = messageBody

    # Record the MIME types of both parts - text/plain and text/html
    part1 = MIMEText(text, 'plain')
    part2 = MIMEText(html, 'html')
    
    # Attach parts into message container.
    # According to RFC 2046, the last part of a multipart message, in this case
    # the HTML message, is best and preferred.
    msg.attach(part1)
    msg.attach(part2)

    # Send the message via local SMTP server.
    s = smtplib.SMTP('localhost')
    # sendmail function takes 3 arguments: sender's address, recipient's address
    # and message to send - here it is sent as one string.
    if DEBUG < 2:
        try:
            print ("\tSending email...")
            myDict = s.sendmail(msgSender, recipients, msg.as_string())
            if not myDict: print ("\tEmail sent!")
            else: print("Something unexpected happened while sending email")
            #else: import pdb; pdb.set_trace()
        
        except Exception as e:
            print ("Unexpected error sending mail:", e)    
            
        finally:
            s.quit()
    else:
        print (msgSender, recipients, msg.as_string())


#####################################
# Read from json file
#
    #def getJsonData():
    #    global myJsonFile, DEBUG
    #    with myJsonFile.open() as data_file:
    #	    data = json.load(data_file)
    #	    data_file.close()
    #    return data
## Error checking experiments
#try:
#  print (data["BlockOwnersEmailAddr"]["BOGUS"])
#except (KeyError):
#  print ("Error caught!")
#
#if "TEST" in data["BlockOwnersEmailAddr"]:
#  print ("'TEST' is here.")





####################################################
# Function: queryAppendRegNames(list): return string
#
#Takes a list (of blocks) as input and returns 
# an sql query of type string intended to run 
# with cursor for sql query
#
#Generates query for last x distinct regression 
# names. User must replace BLOCK {blk} and 
# TABLE{table}
####################################################
def queryAppendRegNames(blkLabels, query):
    if DEBUG: print ("\n\tInside function 'queryAppendRegNames' of ", __name__)
    if DEBUG: print ("Entering queryAppendRegNames func to create query")
    if len(blkLabels) < 1: raise SystemError
    if DEBUG > 4: print (blkLabels)
    #################################################
    #This code generates what to append to the query#
    #
    query += " AND ("
    for _ in range(len(blkLabels) - 1):
        query += "\n  Regression_name = '{}' OR".format(blkLabels.pop())
    query += "\n  Regression_name = '{}')".format(blkLabels.pop())
    query += "\n ORDER BY Regression_name DESC"
    #
    #################################################
    if DEBUG: print (query)
    if DEBUG > 4: print ("Exiting queryAppendRegNames")
    return query





################################################
# Function: getBlocks(pymssql.Cursor, 
#   pymssql.Cursor, string)
# return set
#
#Pass the open connection pymssql.Cursor obect
# along with the database table (as string) as
# input. Function returns blocks present in the
# table of the database in set format
#
#Note: when calling this func, always wrap in 
#try/except/finally clause closing the db conn
################################################
def getBlocks(db,cursor,t, JNAME,data,BlockNameQuery):
    if DEBUG: print ("Entering getBlocks func for table {}".format(t))
#    global JNAME, data, BlockNameQuery
    blkSet = set()
    query = data[JNAME][BlockNameQuery].format(table=t)
    if DEBUG > 4: 
      print ("\n\tLocal variable query")
      print (query)

    ## Execute sql query
    cursor.execute(query)
    #
    ################################################
    ## Inner Loop to check results for current block
    # Fetch first row from results
    row = cursor.fetchone()
    while row:
        blkSet.add(''.join(row))
        row = cursor.fetchone()
    if DEBUG > 2: print (' '.join(blkSet))
    return blkSet


def getBlocks2(db,cursor,query):
    if DEBUG > 2: print ("Get blocks from query:", query)
    blkSet = set()
    ## Execute sql query
    cursor.execute(query)
    #
    ################################################
    ## Inner Loop to check results for current block
    # Fetch first row from results
    row = cursor.fetchone()
#    import pdb; pdb.set_trace()
    while row:
        blkSet.add(row[0])
        row = cursor.fetchone()
    if DEBUG > 2: print ("Blocks returned from table:", ' '.join(blkSet))
    return blkSet





################################################
# Function: getLastRegressionLabel
################################################
def getLastRegressionLabel(db,cursor,query):
    ##
    if DEBUG > 4: print (query)
    
    #####################
    # Execute sql query #
    cursor.execute(query)
    
    ################################################
    ## Inner Loop to check results for current block
    # Fetch first row from results
    row = cursor.fetchone()
    if row:
        if DEBUG > 4: print (row)
        block,regName,regResults,regDate = row
        return regName
    else:
        return
        


################################################
# Function: printPretty
################################################
def printPretty(records,num,title='Summary:'):
    #import pdb; pdb.set_trace()
    if isinstance(records, list):
        #TODO: find max len of strings in list and use that number instead of 120
        print ("\n{}\n{}".format(title.center(120),"="*120))
        table = list()
        for i in records:
            msg = ""
            for n in range(num):
                msg += "{:35} ".format(i[n])
            table.append(msg)
        for i in table:
            print (i)
     
    elif isinstance(records, dict):
        for key in records:
            if isinstance(records[key], Param):
                for i in records[key]:
                    print (i)
            print ("")

    print ("")


        
################################################
# Function: runShellCmd
################################################
import subprocess, sys
def runShellCmd(command, exec_shell='/bin/tcsh', returnOutput=True, ignoreError=True):
    print ("\n\tInside function 'runShellCmd' of ", __name__) 
    print ("command:",command)

    myCompletedProcess = subprocess.run(command, shell=True, universal_newlines=True, executable=exec_shell, stdout=subprocess.PIPE, stderr=subprocess.PIPE)

    if ignoreError is False and myCompletedProcess.returncode > 0:
        print (myCompletedProcess)
        assert SystemError

    if not returnOutput:
        return
    
    output = myCompletedProcess.stdout
    if output:
        if (DEBUG > 2 and len(output.split('\n')) < 100): print (output)
        return output.strip()
    else:
        return None
#    try:
#        if len(output.strip().split('\n')) is 1:
#            return output.strip()
#        else:
#            return myCompletedProcess.stdout.strip().split('\n')
    ###
#    except subprocess.CalledProcessError as e: #not needed since we're not checking output of stderr
#        print ("Shell command resulted in error:",e)
#        return

#    except AttributeError:
#        print ("Shell command returned nothing")

#    except:
#        print ("Shell command returned unexpected error:",sys.exc_info())
#        raise SystemError


#def runShellCmd(command, exec_shell='/bin/tcsh'):
#    if DEBUG > 4: print ("runShellCmd:",command)
#    try:
#        output = subprocess.check_output(command, shell=True, universal_newlines=True, executable=exec_shell)
#        return output
#    except subprocess.CalledProcessError as e:
#        print ("Shell returned nothing:",e)
#        return
#    except:
#        print ("Shell returned nothing:",sys.exc_info())
#        raise SystemError


