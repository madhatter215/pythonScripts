#!/pkg/qct/software/python/3.5.2/bin/python

###############################################################################
# Send Email
#https://docs.python.org/3/library/email-examples.html
###############################################################################
import sys                      # Std Lib: used here to print error message
import json                     # Std Lib: used to import email addr of blk owners
import smtplib                  # Std Lib: email server
from email.mime.multipart \
        import MIMEMultipart    # Std Lib: email msg
from email.mime.text \
        import MIMEText         # Std Lib: email msg
import setup.config as config   # local app: top level config variables
#import helper.myfunc as myfunc # local app: keep common functions there



## Global Variabls
DEBUG           = config.DEBUG
#DEBUG = 3 #Override
JNAME           = 'BlockOwnersEmailAddr'
PROJ            = config.PROJ
projectName     = config.projectName
projAlias = projectName if (projectName != 'napier') else 'Napier AX' #Nickname for napier on main branch
sender          = config.emailSenderOrigin
carbonCopy      = config.emailCarbonCopy
emailOnlyMe     = config.emailOnlyMe

HTMLRed         = '#E84659'
HTMLGreen       = '#60B152'
HTMLTableWidth  = '800px'



######################################
## Get json data from global config ##
data = config.myJsonData
if DEBUG > 4:
    for i in data[JNAME]:
        print ("Email owner for '%s' = '%s'" %(i, data[JNAME][i]))
#######################################




###########################################################################
##                          Function Definitions                         ##
###########################################################################


########################################
#Takes a list of blocknames as input,
#iterates over list and calls sendMail
#for each block
def dispatchEmails(stuffToUnpack):
    if DEBUG: print ("\n\tInside function 'dispatchEmails' of ",__name__)
#    stuffToUnpack.reverse()
    if DEBUG > 4: print (stuffToUnpack)
    myListOfRows = list()
    for x in stuffToUnpack:
        if DEBUG > 4: print ("\nProcessing record:", x)
        t,block,myListOfRows = x
        if DEBUG > 2: print ("\nBlock:",block)
#        import pdb; pdb.set_trace()
        if block:
            bodyOfMsg = createHTML(block,myListOfRows,t)
            sendMail(block,bodyOfMsg)
        else:
            pass
#        for row in myListOfRows:
#            block,regName,regResults,regDate = row
#            if DEBUG: print ("\tregName={0},regResults={1},regDate={2}".format(
#                                regName,regResults,regDate))
#        if DEBUG > 3: print ("Block = ",block)
#        block = block.replace('_NAPIER','')
#        if data[JNAME][block]:
#            print ("\nYES, email sending for ", block, PROJ)
#            sendMail(block)
#        else:
#            print ("NO block named {} or no email addr give for block owner".format(block+PROJ))



#######################################################################
#Top, Middle, Bottom HTML chunks combine to form the HTML Message
#######################################################################
def createHTML(block,myListOfRows,t):
    if DEBUG: print ("\n\tInside function 'createHTML' of ", __name__)
    if 'mini' in t.lower(): 
        dbTableName = "Mini Regression"
    elif 'full' in t.lower(): 
        dbTableName = "Full Regression"

    ################################
    ## TOP: Header of HTML for Email
    top = '''\
<html>
<head>{block}</head>
<body>
<br>
<br>
<span style="margin-left: 10px;color:black ; font-weight: bold;font-size: 24px;text-align:center;">Regression Results for {block} {dbtable}</span>
    <table cellspacing="0" align="Left" border="1" style="color: #333333;border-color: #99CCFF;font-family: Calibri;font-weight: bold;
    width: {table_width};margin-left: 10px;border-collapse: collapse;">
    <tbody><tr align="center" style="color:White;background-color:#507CD1;font-size:16px;font-weight:bold;">
        <th scope="col">Block</th>
        <th scope="col">Timestamp</th>
        <th scope="col">Label</th>
        <th scope="col">Result</th>
        <th scope="col">TotalTC</th>
        <th scope="col">PassRate%</th>
'''.format(block=block,dbtable=dbTableName,table_width=HTMLTableWidth)
#############
    
    ##################################################
    ## BOTTOM: Static, just closes the HTML table/body
    bottom = '''\
    </tr></tbody>
    </table>
</body>
</html>
'''
#############
    

    ###########
    ## MIDDLE
    middle = ''
    
    ########################################
    #Work the middle
    if DEBUG > 4: print ("Length of records = ",len(myListOfRows))
    if DEBUG > 4: print (myListOfRows)
    for row in myListOfRows:
        block,regName,regResults,regTotalTC,regPassRate,regDate = row
        if DEBUG > 2: print ("\tregName={},regResults={},regTotalTC={},regPassRate={},regDate={}".format(
                            regName,regResults,regTotalTC,regPassRate,regDate))
        if "PASS" not in regResults.upper(): # ~pass -> failed
            color = HTMLRed
        else:
            color = HTMLGreen
#        import pdb; pdb.set_trace()
        middle += '''\
        </tr><tr align="center" style="background-color:#EFF3FB;font-size:14px;">
        <td>
                <span>{block}</span>
            </td><td style="text-align:center;">
                <span bold="true">{regDate}</span>
            </td><td style="text-align:left;background-color:{color};">
                <span>{regName}</span>
            </td><td style="text-align:center;background-color:{color};">
                <span>{regResults}</span>
            </td><td style="text-align:center;background-color:{color};">
                <span>{regTotalTC}</span>
            </td><td style="text-align:center;background-color:{color};">
                <span>{regPassRate}</span>
        </td>
        '''.format(block=block,regName=regName,regResults=regResults,regTotalTC=regTotalTC,regPassRate=regPassRate,regDate=regDate,color=color)
    #
    #if DEBUG > 4: print (middle)
    return (top+middle+bottom)





#######################################################################
#Not intended to be called directly, use dispatchEmails and pass a list
#dispatchEmails performs some checking first
def sendMail(block,messageBody):
    if DEBUG: print ("\n\tInside function 'sendMail' of ", __name__)
#    blockRootName = block.upper().replace('_NAPIER','')
    blockRootName = block.upper().split('_')[0]
    if DEBUG > 4: print ("block={}, blockRootName={}, PROJ={}".format(block, blockRootName, PROJ))

    if not DEBUG:
        try:
          recipients = data[JNAME][blockRootName].split(', ')
        except (KeyError):
          recipients = list()
        finally:
          for i in carbonCopy.split(', '):
            recipients.append(i)
    else:
        recipients = [emailOnlyMe]

#    print (type(recipients))
#    import builtins
#    if isinstance(recipients, builtins.list):
#        print ("TRUE!!!")


    if "Mini Regression" in messageBody:
        dbTableName = "Mini Regression"
    elif "Full Regression" in messageBody:
        dbTableName = "Full Regression"
    
    # Create message container - the correct MIME type is multipart/alternative.
    msg = MIMEMultipart('alternative')
    msg['Subject'] = "{project} - Consecutive Regression Failure: {blk} {regName}".format(\
                                            project=projAlias,blk=block,regName=dbTableName)
    msg['From'] = sender
    msg['To'] = ', '.join(recipients)
    ##
#    if DEBUG: 
    print ("\tFrom:{sendr}\n\tTo:{to}".format(sendr=msg['From'],to=msg['To']))
    print ("\tRecipients:{recip}\n\tSubject:{subj}".format(
        recip=recipients,subj=msg['Subject']))
    # Create the body of the message (a plain-text and an HTML version).
    #
    ##
    text = ""
    html = messageBody
#    ###############################################################################
#    #Chris - I know the next line of code looks fancy and all. All it does is
#    # a) separate the string of email addresses on ', '
#    # b) get the userid part of the email addresses (before "@qualcomm.com")
#    # c) and combine them into a string again with "/" to print the names of 
#    #each block owner in the body of the message
#    html = html.format(('/'.join(list(
#        map((lambda x: x.split('@')[0]), data[JNAME][block].split(
#        ', '))))))

    # Record the MIME types of both parts - text/plain and text/html
    part1 = MIMEText(text, 'plain')
    part2 = MIMEText(html, 'html')
    #if DEBUG > 3: print (part2)
    
    # Attach parts into message container.
    # According to RFC 2046, the last part of a multipart message, in this case
    # the HTML message, is best and preferred.
    msg.attach(part1)
    msg.attach(part2)

    # Send the message via local SMTP server.
    s = smtplib.SMTP('localhost')
    # sendmail function takes 3 arguments: sender's address, recipient's address
    # and message to send - here it is sent as one string.
    #s.sendmail(sender, recipients, msg.as_string())
    try:     
        if DEBUG < 2:
            print ("\tSending email...")
            myDict = s.sendmail(sender, recipients, msg.as_string())
            if not myDict: print ("\tEmail sent!")
            else: raise
        else: print ("Debug option found, no email will be sent")
    
    except Exception as e:
        print ("Unexpected error sending mail:", e)    
        
    finally: s.quit()



##
    print ("")
##

#import pdb; pdb.set_trace()

# SQL Query
#import collections  #used for storing query results into named tuple
#import operator     #used for sorting named tuples

# specify the database to use
#Not needed when database is specified in pymssql.connect()
#cursor.execute("use Helium;")

#from datetime import datetime
#y=datetime.strptime(mystr, '%Y-%m-%d')
#y.strftime("%B %d %Y"

#table = tuple("".split(','))
#Date,Block,Regression_name,Timestamp,Deliverby,Reg_result,TotalTC,PassTC,FailTC,IncompleteTC,InconclusiveTC,weblink,PassRate,BLDate,RegressionTime,DesignBL,Label_notes,Wmac_design,Wmac_verif,Wmac_int,ius_reg_status,label_rule,label_rule_link


