#!/pkg/qct/software/python/3.5.2/bin/python

###################################################################################
# Filename: emailDiskAbusers.py
# Author: cskebriti
# Description: Standalone program, does NOT require setup/config.py
#
''' Takes the argument passed from command line and runs a check to find users 
who take up the most disk space, sending notification email to them.
Ex. Usage:
  ./emailDiskAbusers.py /prj/qca/cores/wifi/lithium/santaclara/dev01/workspaces

'''
###################################################################################
import sys, os
import collections, operator
import subprocess
from pathlib import Path
import smtplib                  # Std Lib: email server
from email.mime.multipart \
        import MIMEMultipart    # Std Lib: email msg
from email.mime.text \
        import MIMEText         # Std Lib: email msg



#####################################################################################################
##     Global Variables       
#####################################################################################################
DEBUG           = 0
SENDER          = "RegressionAutomation@DoNotReply.com"
mainDirectory   = Path("/prj/qca/cores/wifi/lithium/santaclara/dev01/workspaces/") #default

USER_PERCENT_USAGE_THRESHOLD    = 75.0
DISK_CAPACITY_THRESHOLD         = 85.0


#Named Tuple
DiskUsages      = collections.namedtuple('DiskUsages', 'user spaceUsed spaceLimit usedPercent')
#
records         = list() #keep a list of type DiskUsages
ToList = list()
CcList = ["c_ckebri@qti.qualcomm.com", "tpillai@qti.qualcomm.com", "lithium.qdisk@qca.qualcomm.com"]
##

HtmlBody = '''
<!DOCTYPE html>
<html>
	<head>
		<meta charset="UTF-8">
			<title>Excel To HTML using codebeautify.org</title>
		</head>
		<body>
			<style type=\"text/css\">
                .one {border-collapse:collapse;table-layout:fixed;COLOR: black; width: 1000px;word-wrap: break-word;}
			    .b { border-style:solid; border-width:3px;border-color:#333333;padding:10px;width:10px;background-color:#2E64FE; text-align:center;COLOR: black;}
			    .c { border-style:solid; border-width:3px;border-color:#333333;text-align: center;padding:10px;background-color:#ffffff;width:10px;COLOR: black;}
			    .d { border-style:solid; border-width:3px;border-color:#333333;text-align: left;padding:10px;background-color:#79d379;width:10px;COLOR: black;}
			    .red { border-style:solid; border-width:3px;border-color:#333333;text-align: left; padding:10px;background-color:#ff704d;width:10px;COLOR: black;}
			    .yellow { border-style:solid; border-width:3px;border-color:#333333;text-align: center;padding:10px;background-color:#ffff80;width:10px;COLOR: black;} 
			    .green { border-style:solid; border-width:3px;border-color:#333333;text-align: left;padding:10px;background-color:#66ff66;width:10px;COLOR: black;}
			    .grey { border-style:solid; border-width:3px;border-color:#333333;text-align: left;padding:10px;background-color:#e0e0d1;width:10px;COLOR: black;}
            </style>
			<H5>Hello,
				
				<br/>Please be aware that other engineers share the same disk as you. As a consideration, please utilize this time now to remove any unused files in 
				        your workspace to free disk space for the group.
				
				<br/>
				<br/>
			</H5>
			<table class=\"one\">
				<tr>
					<th class=\"b\">USER</th>
					<th class=\"b\">SPACE USED MB</th>
					<th class=\"b\">SPACE LIMIT MB</th>
					<th class=\"b\">USED PERCENT</th>
				</tr>
'''

HtmlTableTemplate = '''
                <tr> 
                    <td class=\"c\">{user}</td>
                    <td class=\"c\">{spaceUsed}</td>
                    <td class=\"c\">{spaceLimit}</td>
                    <td class=\"c\">{usedPercent}</td>
                </tr>
'''

Signature = '''
			</table>
			<br/>
			<br/>Best Regards,
			
			<br/>Automation Team


		
		</body>
	</html>
'''


#####################################################################################################
# Function Definitions:
#####################################################################################################

#################################
def getDiskAbusers():
    global records,ToList
    
    cmd = "/pkg/icetools/bin/quota.eng -u all -d {}".format(mainDirectory)
    output = (subprocess.check_output(cmd, shell=True, universal_newlines=True)).split('\n')
    
    for line in output:
        
        try:
            itype,user,spaceUsed,spaceLimit,usedPercent,filesUsed,filesLimit,fUsedPercent = line.split()
            #import pdb; pdb.set_trace()
            if ( (itype == 'user') and (float(usedPercent) > USER_PERCENT_USAGE_THRESHOLD) ):
                r = DiskUsages(user,float(spaceUsed),float(spaceLimit),float(usedPercent))
                if user.isalpha():
                    records.append(r)
                    ToList.append(user+'@qti.qualcomm.com')

        except ValueError:
            continue


#################################
def createMsgBody(user, spaceUsed, spaceLimit, usedPercent):
    HtmlMsg = HtmlBody + HtmlTableTemplate.format(
        user=user, spaceUsed=spaceUsed, spaceLimit=spaceLimit, usedPercent=usedPercent)
    #print (HtmlMsg + "\n\n")
    return HtmlMsg + Signature


#################################
def emailUser(record):
    assert(isinstance(record,DiskUsages)),"Internal Error"
    
    ##
    userEmail = record.user + "@qti.qualcomm.com" #, "tpillai@qti.qualcomm.com"
    recipients = [userEmail, "c_ckebri@qti.qualcomm.com"] \
        if not DEBUG else ["c_ckebri@qti.qualcomm.com"] #list

    # Create message container - the correct MIME type is multipart/alternative.
    msg = MIMEMultipart('alternative')
    msg['Subject']  = "HIGH Disk Usage Warning: '{user}' on {idir}".format(
                        user=record.user,idir='/'.join(mainDirectory.parts[-3:]))
    msg['From']     = SENDER
    msg['To']       = ', '.join(recipients) #type string

    # Generate Html Message
    messageBody = createMsgBody(record.user,record.spaceUsed,record.spaceLimit,record.usedPercent)

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

    try:
        print ("\tSending email...")
        myDict = s.sendmail(SENDER, recipients, msg.as_string())
        if not myDict: print ("\tEmail sent!")
        else: print("Something unexpected happened while sending email")
        #else: import pdb; pdb.set_trace()
    
    except Exception as e:
        print ("Unexpected error sending mail:", e)    
        
    finally:
        s.quit()


#################################
def dispatchEmails():
    if not DEBUG:
        for record in records:
            emailUser(record)
    else:
        #emailUser(records[0])
        pass
    ##
    print("\nNumber of records:", len(records))


#################################
def checkInputArgs():
    global mainDirectory
    if len(sys.argv) <= 1:
        print ("Usage: {} <DIRECTORY>".format(sys.argv[0]))
        print ("using default directory:", mainDirectory)
    #    raise SystemExit
    else:
        mainDirectory = Path(sys.argv[1])
        assert(mainDirectory.exists()),"Path '{}' does not exist".format(mainDirectory)


#################################
def createSummary():
    mySorted = sorted(records, key=operator.attrgetter('spaceUsed', 'usedPercent', 'user'), reverse=True)
    MsgSummaryBody = ""
    for row in mySorted:
        MsgSummaryBody += HtmlTableTemplate.format(user         = row.user, 
                                                   spaceUsed    = row.spaceUsed, 
                                                   spaceLimit   = row.spaceLimit, 
                                                   usedPercent  = row.usedPercent)
    ##
    HtmlSummary = HtmlBody + MsgSummaryBody + Signature
    return HtmlSummary
    
#################################
def emailSummary(SummaryMsg):
    ##
    if not DEBUG:
        recipients = ToList + CcList
    else: #debug
        recipients = ["c_ckebri@qti.qualcomm.com"] #list
        print (ToList)

    #For subject of message
    diskCapacity = getDiskCapacity()
    idir = '/'.join(mainDirectory.parts[-3:])
    
    # Create message container - the correct MIME type is multipart/alternative.
    msg = MIMEMultipart('alternative')
    msg['Subject']  = "HIGH Disk Usage Summary on {0} ({1}% capacity)".format(
                        idir, diskCapacity)
    msg['From']     = SENDER
    msg['To']       = ', '.join(recipients) #type string

    # Generate Html Message
    messageBody = SummaryMsg

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

    try:
        print ("\tSending email...")
        myDict = s.sendmail(SENDER, recipients, msg.as_string())
        if not myDict: print ("\tEmail sent!")
        else: print("Something unexpected happened while sending email")
        #else: import pdb; pdb.set_trace()
    
    except Exception as e:
        print ("Unexpected error sending mail:", e)    
        
    finally:
        s.quit()


#################################
def getDiskCapacity():
    cmd = "df --si {0} | xargs | tr -s ' ' | cut -d ' ' -f 12".format(mainDirectory)
    output = float(subprocess.check_output(cmd, shell=True, universal_newlines=True).split('%')[0])
    return output


#################################
def checkDiskCapacity_bool():
    output = getDiskCapacity()
    if output > DISK_CAPACITY_THRESHOLD:
        return True
    else: return False


#####################################################################################################
# Main: Start of Program                                                                            #
#####################################################################################################
if 'main' in __name__: print ("Start of Program")

##
checkInputArgs()
#
getDiskAbusers()
#
if checkDiskCapacity_bool(): 
    #dispatchEmails() #thangam said dont run this
    emailSummary(createSummary())
#
#####################################################################################################





