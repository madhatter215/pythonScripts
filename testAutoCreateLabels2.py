#!/pkg/qct/software/python/3.6.0/bin/python

import os, subprocess, sys
import collections, operator
from pathlib import Path
import time
import setup.config as config
import helper.p4_functions as p4_functions
import random
import helper.myfunc as utils
import shutil
import re

#BLOCK = ''
#if (not config.BLOCK) and (sys.argv[1]):
#    BLOCK = sys.argv[1]
#    if 'napier' not in BLOCK:
#        print ("Only napier is supported: Exiting")
#        raise SystemExit

#elif config.BLOCK:
#    BLOCK = config.BLOCK

#else:
#    print ("Need to pass an argument: e.g. {} rxdma_napier".format(sys.argv[0]))
#    raise SystemExit


#P4ClientFile            = '/tmp/p4clienttest.txt'
PREFIX_TEMPLATE         = 'autolabel_napier2hawkeye'
PREFIX                  = ''
DISK                    = 'regress01'
#P4_WORKSPACE            = Path('/prj/qca/cores/wifi/lithium/santaclara/regress01/workspaces/c_ckebri/test_autolabel_napier2hawkeye')
#DEPOT                   = 'lithium'
PRJ                     = '_napier'
NapierInputStruct       = dict()#set()
HawkeyeInputStruct      = dict()#set()
PROJ_PATH               = '/prj/qca/cores/wifi/lithium/santaclara'
HELIUM_TOOLS            = '/prj/helium_tools/lithium'

DEPOT       = config.DEPOT
NAPIER      = config.NAPIER
DEBUG       = config.DEBUG
BLOCK       = config.BLOCK
P4CLIENT    = config.P4CLIENT
NOCLEAN     = config.NOCLEAN
CLEAN = True if not NOCLEAN else False
NAPIER_VERIF_LABEL_TO_SYNC = config.P4LABEL
print (BLOCK,NAPIER_VERIF_LABEL_TO_SYNC)
if BLOCK == '':
    print ("**Script needs block passed as input, Exiting...")
    raise SystemExit
assert(NAPIER), "\n\nOnly Napier project is supported."
assert(PRJ in BLOCK), "\n\n**Currently this script only supports Napier to Hawkeye conversion."

Block  = collections.namedtuple('Block', 'blockname \
napierLabelname napierVerifInfoFile napierCommonVerifFile napierDesignFile \
hawkeyeLabelname hawkeyeVerifInfoFile hawkeyeCommonVerifFile hawkeyeDesignFile')

#Named Tuple
Param = collections.namedtuple('Param', '\
blk \
depotPathToVerif \
relPathToVerif \
labelsyncName \
MINI_REG_CMD \
verifInfoFile \
designInfoFile \
prjSourceFile \
blkSourceFile \
')


########################################################################
# Function Definitions:
########################################################################
def setLithiumP4Env(depot):
    os.environ['PATH'] += os.pathsep + '/pkg/qct/software/p4'
    os.environ['P4PORT']        = "p2.qca.qualcomm.com:1666"
    os.environ['DEPOT_IP_TOP']  = '//depot/prj/qca/' + depot

def setPrefix(prefix,block):
    return prefix + '_' + block + '_' + os.environ.get('USER') + '_' + time.strftime("%Y%m%d_%H%M") + '_rand' + str(random.randrange(1000))

def createWorkspaceDir(prefix, disk):
    workspace = Path("{0}/{1}/workspaces/{2}/".format(PROJ_PATH, disk, os.environ.get('USER')) + prefix)
    workspace.mkdir(mode=0o777, parents=True, exist_ok=True)
    os.chdir(str(workspace))
    os.environ['PROJECTS_HOME'] = os.getcwd()

def createP4Client(prefix):
    assert(prefix), "No prefix"
    os.environ['P4CLIENT'] = prefix
    #import pdb; pdb.set_trace()
    p4Input = p4_functions.P4CLIENT_TEMPLATE.format(
            prefix          = prefix,
            user            = os.environ.get('USER'),
            projectsHome    = os.environ.get('PROJECTS_HOME'),
            depotIpTop      = os.environ.get('DEPOT_IP_TOP') )
    p4Input = p4Input.replace('\n', r'\n')
    command = "echo '{}' | p4 client -i".format(p4Input)
    output = utils.runShellCmd(command)
    if not('saved.' in output or 'not changed.' in output):
        print ("Could not create the P4 client")
        raise SystemError
    #
    ##

def sourceProjFiles(p4sync_bool=True, a='setup/setup_qca.cshrc', b='setup/config_asic.sh'):
    #import pdb; pdb.set_trace()
#    if (CLEAN and p4sync_bool):
#        print ("Running P4 to clean workspace")
#        utils.runShellCmd("p4 sync $DEPOT_IP_TOP/...#none", returnOutput=False)

    if p4sync_bool:
        print ("Sync p4 setup/ and scripts/")
        utils.runShellCmd("p4 sync $DEPOT_IP_TOP/setup/..."     ,returnOutput=False)
        utils.runShellCmd("p4 sync $DEPOT_IP_TOP/scripts/..."   ,returnOutput=False)

    '''
    Basically, need to source a) setup_qca.cshrc and b) config_asic.sh then load env
    The approach below isn't perfect but it works for most env settings
    '''
    command  = "source $PROJECTS_HOME/{0} > & /dev/null && source $PROJECTS_HOME/{1} > & /dev/null ; env"
    output   = utils.runShellCmd(command.format(a, b))
    lines    = output.split('\n')

    for line in lines:
        line = line.strip()
        if '=' in line:
          array = line.split('=')
          var = array[0]
          val = ''.join(array[1:])
          os.environ[var] = val
    #
    ##

def getInputFileStruct():
    global NapierInputStruct,HawkeyeInputStruct
    
    ##Napier#
    output = utils.runShellCmd(r"cat {0}/scripts/lithium_reg_input.txt | grep -iE '^\S+?(_napier):://' \
            ".format(HELIUM_TOOLS))#| cut -d: -f 1,8,9,10,11")
    inputFileStructHelper(output,NapierInputStruct)

    ##Hawkeye#
    output = utils.runShellCmd(r"cat {0}/scripts/lithium_reg_input.txt | grep -viE '^\S+?(_napier):://' \
            ".format(HELIUM_TOOLS))#| cut -d: -f 1,8,9,10,11")
    inputFileStructHelper(output,HawkeyeInputStruct)


def inputFileStructHelper(output,struct):
    lines = output.split()
    for i in lines:
        try:
            blk,depotPathToVerif,relPathToVerif,MINI_REG_CMD,verifInfoFile,designInfoFile,prjSourceFile,blkSourceFile = i.split('::')
            labelsyncName = '@lithium_wcss_core_' + blk + '_label_recommended'
            newParam = Param(
                                blk              = blk,
                                depotPathToVerif = depotPathToVerif,
                                relPathToVerif   = relPathToVerif[1:],
                                labelsyncName    = labelsyncName,
                                MINI_REG_CMD     = MINI_REG_CMD,
                                verifInfoFile    = verifInfoFile,
                                designInfoFile   = designInfoFile,
                                prjSourceFile    = prjSourceFile,
                                blkSourceFile    = blkSourceFile )

            if blk not in struct:
                struct.update({blk: newParam})
            ###
        ##
        except ValueError as e:
            if DEBUG > 3: print ("\n\t{0}:\n{1}\n".format(e,i))
        ###
        
def sendMail(subj,failedCmd=''):
    
    command = \
"echo 'prefix: {0}\r \
NapierVerif={3},\r \
VerifCommon={4},\r \
HKDesignFile={5},\r \
Command={7}' \
| mail -s '[Auto-Create Label] {1}: {6}' {2}"
    ##
    command = command.format(
                    PREFIX, 
                    re.sub('_napier','',BLOCK), 
                    config.emailOnlyMe,
                    NP_VERIF_INFO_FILE_PATH.split('/')[-1],
                    VERIF_COMMON_LABEL.split('/')[-1], 
                    HK_DESIGN_LABEL.split('/')[-1],
                    subj, failedCmd )
    #
    utils.runShellCmd(command, returnOutput=False)
    ####


################################################################################################################################
# MAIN:
################################################################################################################################
#TODO: Start by checking diskspace

try:

    setLithiumP4Env(DEPOT)
    PREFIX  = setPrefix(PREFIX_TEMPLATE,BLOCK) if not P4CLIENT else P4CLIENT
    createWorkspaceDir(PREFIX,DISK)
    createP4Client(PREFIX)
    print ("prefix:",PREFIX)
    sourceProjFiles()


    getInputFileStruct()##

    if DEBUG > 3:
        utils.printPretty(HawkeyeInputStruct,3,"Hawkeye Summary:")
        utils.printPretty(NapierInputStruct, 3,"Napier Summary:" )

#import pdb; pdb.set_trace()
#############################################################
# Setup:
# ==========
    NapObj = NapierInputStruct[BLOCK]
    NP_VERIF_INFO_FILE_PATH = NAPIER_VERIF_LABEL_TO_SYNC if NAPIER_VERIF_LABEL_TO_SYNC \
        else p4_functions.getAndParseRecommendedLabel(labelsyncName=NapObj.labelsyncName)
    VERIF_COMMON_FILE = NapObj.verifInfoFile.replace('NAPIER','COMMON')
    HKObj = HawkeyeInputStruct[BLOCK.replace('_napier','')]
    HK_VERIF_INFO_FILE_PATH  = "{}/{}".format(HKObj.relPathToVerif, HKObj.verifInfoFile)
    ##
    VERIF_COMMON_LABEL  = ''
    HK_DESIGN_LABEL     = ''
    NP_DESIGN_LABEL     = ''
    ###


    print ("\n\n\t1) get verif common label for napier; Note: use verif name and replace 'NAPIER' with 'COMMON' to find verif common label")
    command = "p4 print {verifInfoFile} | grep {verifCommonFile}".format(verifInfoFile=NP_VERIF_INFO_FILE_PATH, verifCommonFile=VERIF_COMMON_FILE)
    VERIF_COMMON_LABEL = utils.runShellCmd(command)


    print ("\n\n\t2) get napier design label")
    command = "p4 print {verifInfoFile} | grep {designInfoFile}".format(verifInfoFile=NP_VERIF_INFO_FILE_PATH, designInfoFile=NapObj.designInfoFile)
    NP_DESIGN_LABEL = utils.runShellCmd(command)


    print ("\n\n\t3) get timestamp of napier design label")
    command = "p4 filelog -t {} | grep '^... #{}'".format(NP_DESIGN_LABEL.split('#')[0], NP_DESIGN_LABEL.split('#')[1])
    temp = utils.runShellCmd(command)
    timestamp = temp.split()[6]


    print ("\n\n\t4.a) get HK design file path")
    command = "p4 print $DEPOT_IP_TOP/{verifFilePath} | grep {designInfoFile}".format(verifFilePath=HK_VERIF_INFO_FILE_PATH, designInfoFile=HKObj.designInfoFile)
    z = utils.runShellCmd(command)
    HK_DESIGN_INFO_FILE_PATH = z.split('#')[0]
    del(z)


    print ("\n\n\t4.b) find HK design label with corresponding timestamp")
    command = "p4 filelog -t {designFilePath} | grep ' {timestamp}'".format(designFilePath=HK_DESIGN_INFO_FILE_PATH, timestamp=timestamp)
    temp = utils.runShellCmd(command)
    try:
        y = temp.split()[1] #TODO: handle case where p4 filelog returns multiple turn-ins on the same day, currently it takes last one of the day
        print ("Corresponding HK design found:", temp)
        HK_DESIGN_LABEL = HK_DESIGN_INFO_FILE_PATH + y
        del(y)
    except AttributeError:
        print ("Error: Could not find corresponding Hawkeye design of the same timestamp")
        sendMail("Could not find corresponding HK design", command)
        raise SystemError


    print ("\n\n\t5) sync to latest verif label on Hawkeye")
    command = "sync.pl $DEPOT_IP_TOP/{}#head".format(HK_VERIF_INFO_FILE_PATH)
    utils.runShellCmd(command,returnOutput=False)


    print ("\n\n\t6) Finally, use sync.pl on VERIF_COMMON and DESIGN in Hawkeye")
    command = "sync.pl -b {}"
    utils.runShellCmd( command.format(VERIF_COMMON_LABEL)   ,returnOutput=False)
    utils.runShellCmd( command.format(HK_DESIGN_LABEL)      ,returnOutput=False) #returns no error but warnings 



    print ("\n\n\t7) Compile and make sure it pass")
    source1 = 'setup/' + HKObj.prjSourceFile
    source2 = HKObj.relPathToVerif + '/scripts/' + HKObj.blkSourceFile
    sourceProjFiles(p4sync_bool=False, a=source1, b=source2)
    #
    ###
    #
    command = "cat {}/scripts/*ciflow.db | grep ^{}".format(HKObj.relPathToVerif, HKObj.MINI_REG_CMD)
    output = utils.runShellCmd(command)
    temp = re.sub(HKObj.MINI_REG_CMD+'\s*:\s*','',output)#remove header param
    regCmd = temp + ' -compile_only'
    #
    ##
    ##########
    os.chdir(HKObj.relPathToVerif + '/scripts/') #chdir 
    ##
    #
    output = utils.runShellCmd(regCmd, ignoreError=False)#.split('\n')
    #
    ##
    os.chdir(os.environ.get('PROJECTS_HOME')) #go back dir
    ##########
    #
    PASS_BOOL = ''
    if bool(re.search('Build Job \w+ returned status: PASS', output)):
        PASS_BOOL = True
        print ("Compile Passed!")
    elif bool(re.search('Build Job \w+ returned status: FAIL', output)):
        PASS_BOOL = False
        print ("Compile FAILED!")
    else: print ("No pass/fail found in compile log!")
    ##
    ####



    print ("\n\n\t8) check-in files to create new label")
    ###
    ##Compile Passed
    if PASS_BOOL is True:
        try:
            command = "update_info.pl {}".format(HK_VERIF_INFO_FILE_PATH)
            output = utils.runShellCmd(command, returnOutput=True, ignoreError=False)
            ##Check output:
            # e.g. '// [INFO  ](Perforce::Files) : successful: '
            assert('success' in output)
            #######
            ##
            command = \
                "p4 submit -d 'Auto-generated: NapierVerif={}, VerifCommon={}, NapierDesignFile={}'".format(
                            NP_VERIF_INFO_FILE_PATH.split('/')[-1],
                            VERIF_COMMON_LABEL.split('/')[-1], 
                            NP_DESIGN_LABEL.split('/')[-1] )
            output = utils.runShellCmd(command, returnOutput=True, ignoreError=False)
            ##Check output:
            # e.g. 'Change 4177970 submitted.\n'
            assert(bool(re.search('Change \d* submitted', output)))
            #######
            ##Success!
            temp = re.search('^edit //.*', output, re.MULTILINE)
            newlySubmittedVerifLabel = temp.group().split('/')[-1]
            sendMail("Submit Successful! (New Hawkeye Label {}".format( newlySubmittedVerifLabel) ,command)
            #Done, all was sucessfull. Jump to step 9
            ###########################################
        
        except (AssertionError, SystemError):
            print ("\n\n***Compile passed but unable to submit new label to p4!\n", output)
            sendMail("Check-in Files Failed",command)
            raise SystemError #Raise error to exit program (jump to outer 'finally' code block)
        ##
        ###
    ###
    ##Compile Failed
    elif PASS_BOOL is False:
        print ("Compile Failed for Block:",BLOCK)
        #TODO:Email block owner
        sendMail("Compile Failed!")
        raise SystemExit
        ##
        ###
    ###
    ##Compile FUBAR'ed
    else:
        print ("\n\n**Internal error, could not determine compile pass/fail from step 7!")
        raise SystemError
    ###
    #####


except:
    print ("\n\n\t***Block '{}' Failed:\n".format(BLOCK), sys.exc_info())


finally:
    print ("\n\n\t9) clean")
    if CLEAN:
        utils.runShellCmd("p4 sync #none")
        shutil.rmtree(path=os.environ.get('PROJECTS_HOME'), ignore_errors=True)
        command = "p4 client -d " + PREFIX
        utils.runShellCmd(command, returnOutput=False)
    else:
        print ("prefix:",PREFIX)



