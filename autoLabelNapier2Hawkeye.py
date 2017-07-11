#!/pkg/qct/software/python/3.6.0/bin/python

import os, subprocess, sys
import collections, operator

BLOCK                   = 'rxdma'
P4ClientFile            = '/tmp/p4clienttest.txt'
DISK                    = 'regress01'
blockSet                = set('txpcu pdg hwsch rxpcu txole rxdma rxole txdma rri crypto gxi sfm'.split())
blockSet = [BLOCK,] #Override
DEPOT                   = 'lithium'
PRJ                     = '_napier'
records                 = set()
#TODO:Change type! Need dictionary key/value pair where value is tuple and key is blockname
NapierInputStruct       = dict()#set()
HawkeyeInputStruct      = dict()#set()

Block  = collections.namedtuple('Block', 'blockname \
napierLabelname napierVerifInfoFile napierCommonVerifFile napierDesignFile \
hawkeyeLabelname hawkeyeVerifInfoFile hawkeyeCommonVerifFile hawkeyeDesignFile')

#Named Tuple
Block = collections.namedtuple('Block', '\
blockname \
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
fullDaysBehindRecommendedLabel \
')

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

UmacSubBlocks = \
"""
PDG
TXDMA
HWSCH
RXDMA
RXPCU
RXOLE
TXPCU
TXOLE
CRYPTO
SFM
LPEC
TQM
REO
WBM
TCL
""".split()


########################################################################
# Function Definitions:
########################################################################
def setLithiumP4Env():
    os.environ['PATH'] += os.pathsep + '/pkg/qct/software/p4'
    os.putenv('P4PORT',         "p2.qca.qualcomm.com:1666")
    os.putenv('DEPOT_IP_TOP',   "//depot/prj/qca/lithium")

def setPrefix():
    return 'test_autolabel_napier2hawkeye'

def createWorkspaceDir(prefix, disk):
    os.chdir("/prj/qca/cores/wifi/lithium/santaclara/{0}/workspaces/{1}/".format(disk, 'c_ckebri') + prefix)

def createP4Client(prefix, p4ClientFile):
    os.putenv('P4CLIENT', prefix)
    subprocess.check_output("p4 client -i < {0}".format(p4ClientFile), shell=True, universal_newlines=True)

def sourceProjFiles():
    '''
    Basically, need to source a) setup_qca.cshrc and b) config_asic.sh then load env
    '''
    output = subprocess.check_output("source setup/setup_qca.cshrc > & /dev/null && source setup/config_asic_28lp.sh > & /dev/null ; env", 
            shell=True, universal_newlines=True, executable='/bin/csh')
    
    for line in output:
        line = line.strip()#chomp
        array = line.split('=')
        var = array[0]
        val = ''.join(array[1:])
        os.putenv(var, "'{0}'".format(val))
    ###



################################################################################################################################
def getLabelVersionsForBlock(blk,struct):##HERE IT IS!!!
    labelname = struct[blk].labelsyncName
    verifInfoFile = getAndParseRecommendedLabel(labelname).split('verif/')[1]
    os.environ['DEPOT_IP_TOP'] + struct[blk].
    commonVerifFile = getCommonVerif(block, )
    designFile = getDesignFile(napierVerifInfoFile, block.upper(), "_28lp")
    

    hawkeyeLabelname = '@lithium_wcss_core_' + block + '_label_recommended'
    hawkeyeVerifInfoFile = getAndParseRecommendedLabel(hawkeyeLabelname)
    hawkeyeCommonVerifFile = getCommonVerif(block, hawkeyeLabelname)
    hawkeyeDesignFile = getDesignFile(hawkeyeVerifInfoFile, block.upper())
    ##
    #
    newBlock = Block(
            blockname               = block, 
            napierLabelname         = napierLabelname, 
            napierVerifInfoFile     = napierVerifInfoFile, 
            napierCommonVerifFile   = napierCommonVerifFile, 
            napierDesignFile        = napierDesignFile,
            hawkeyeLabelname        = hawkeyeLabelname, 
            hawkeyeVerifInfoFile    = hawkeyeVerifInfoFile, 
            hawkeyeCommonVerifFile  = hawkeyeCommonVerifFile, 
            hawkeyeDesignFile       = hawkeyeDesignFile )

    return newBlock
    ###

#def do_something(a):
#    for block in a:
#        napierLabelname = '@lithium_wcss_core_' + block + PRJ + '_label_recommended'
#        napierVerifInfoFile = getAndParseRecommendedLabel(napierLabelname)
#        napierCommonVerifFile = getCommonVerif(block, napierLabelname)
#        napierDesignFile = getDesignFile(napierVerifInfoFile, block.upper(), "_28lp")
#        

#        hawkeyeLabelname = '@lithium_wcss_core_' + block + '_label_recommended'
#        hawkeyeVerifInfoFile = getAndParseRecommendedLabel(hawkeyeLabelname)
#        hawkeyeCommonVerifFile = getCommonVerif(block, hawkeyeLabelname)
#        hawkeyeDesignFile = getDesignFile(hawkeyeVerifInfoFile, block.upper())
#        ##
#        #
#        newBlock = Block(
#                blockname               = block, 
#                napierLabelname         = napierLabelname, 
#                napierVerifInfoFile     = napierVerifInfoFile, 
#                napierCommonVerifFile   = napierCommonVerifFile, 
#                napierDesignFile        = napierDesignFile,
#                hawkeyeLabelname        = hawkeyeLabelname, 
#                hawkeyeVerifInfoFile    = hawkeyeVerifInfoFile, 
#                hawkeyeCommonVerifFile  = hawkeyeCommonVerifFile, 
#                hawkeyeDesignFile       = hawkeyeDesignFile )

#        records.add(newBlock)
#        ###

def getDesignFile(verifInfoFile, upperblock, fabProcess=''):
    output = runShellCmd("p4 print {0} | grep -i '{1}{2}.info#'".format(verifInfoFile, upperblock, fabProcess))
    if output:
        return output.strip()
    else:
        return 'NA'

#def getDesignFileHawkeye(block,verifInfoFile,fabProcess=''):    
#    output = runShellCmd("p4 print {0} | grep -i '{1}{2}.info#'".format(verifInfoFile, block.upper(), fabProcess))
#    if output:
#        return output.strip()
#    elif HawkeyeInputStruct:
#        #import pdb; pdb.set_trace()
#        y = ""
#        for i in NapierInputStruct:
#            if i[0].replace('_napier','') == block.replace('napier',''):
#                y = i
#        if y:
#            print ("y:",y)
#            commonVerifName = y[2]
#            print ("commonVerifName:",commonVerifName)
#            output = runShellCmd("p4 print {0} | grep -i '{1}'".format(x, commonVerifName))
#            if output:
#                return output.strip()
#    return 'NA' #default fallthrough case

#def getDesignFileNapier(block, x):    
#    output = runShellCmd("p4 print {0} | grep -i '{1}{2}.info#'".format(x, block.upper()))
#    if output:
#        return output.strip()
#    elif NapierInputStruct:
#        #import pdb; pdb.set_trace()
#        y = ""
#        for i in NapierInputStruct:
#            if i[0].replace('_napier','') == block.replace('napier',''):
#                y = i
#        if y:
#            print ("y:",y)
#            commonVerifName = y[2]
#            print ("commonVerifName:",commonVerifName)
#            output = runShellCmd("p4 print {0} | grep -i '{1}'".format(x, commonVerifName))
#            if output:
#                return output.strip()
#    return 'NA' #default fallthrough case


def getCommonVerif(a,b):
    #[15:20 c_ckebri:napier/]>p4 print //depot/prj/qca/lithium/ip/wmac/rxdma/verif/IP_RXDMA_VERIF_NAPIER.info | grep 'IP_RXDMA_VERIF_COMMON.info'
    output = runShellCmd("p4 print {} | grep -i '{}#'".format(a,b))
    if output:
        return output.strip()
#    elif NapierInputStruct:
#        #import pdb; pdb.set_trace()
#        y = ""
#        for i in NapierInputStruct:
#            if i[0].replace('_napier','') == block.replace('napier',''):
#                y = i
#        if y:
#            print ("y:",y)
#            commonVerifName = y[1].replace('NAPIER','COMMON')
#            print ("commonVerifName:",commonVerifName)
#            output = runShellCmd("p4 print {0} | grep -i '{1}'".format(x, commonVerifName))
#            if output:
#                return output.strip()
    return 'NA' #default fallthrough case


def getInputFileStruct():
    global NapierInputStruct,HawkeyeInputStruct
    
    ##Napier#
    output = runShellCmd("cat /prj/helium_tools/lithium/scripts/lithium_reg_input.txt | grep -iE '^\S+?(_napier):://' \
            ")#| cut -d: -f 1,8,9,10,11")
    inputFileStructHelper(output,NapierInputStruct)

    ##Hawkeye#
    output = runShellCmd("cat /prj/helium_tools/lithium/scripts/lithium_reg_input.txt | grep -viE '^\S+?(_napier):://' \
            ")#| cut -d: -f 1,8,9,10,11")
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
                                relPathToVerif   = relPathToVerif,
                                labelsyncName    = labelsyncName,
                                MINI_REG_CMD     = MINI_REG_CMD,
                                verifInfoFile    = verifInfoFile,
                                designInfoFile   = designInfoFile,
                                prjSourceFile    = prjSourceFile,
                                blkSourceFile    = blkSourceFile )

        except ValueError as e:
            print ("\n\t{0}:\n{1}\n".format(e,i))
        
        if blk not in struct:
            struct.update({blk: newParam})


def runShellCmd(command):
    print ("runShellCmd:",command)
    try:
        output = subprocess.check_output(command, shell=True, universal_newlines=True)
        return output
    except subprocess.CalledProcessError as e:
        print ("Shell returned nothing:",e)
        return
    except:
        print ("Shell returned nothing:",sys.exc_info())
        raise SystemError


#TODO: replace this with p4_functions        
def getAndParseRecommendedLabel(labelsyncName):
    #if DEBUG > 4: print ("getAndParseRecommendedLabel: labelsyncName = {}".format(labelsyncName))
    output = getP4RecommendedLabels(labelsyncName)
    #if DEBUG > 4: print ("getAndParseRecommendedLabel: output = {}, returning {}".format(output,output.split(' - ')[0]))
    return output.split(' - ')[0]


#TODO: replace this with p4_functions        
def getP4RecommendedLabels(labelsyncName):
    #if DEBUG > 4: print ("getRecommendedLabels: labelsyncName = {}".format(labelsyncName))
    outputLines = subprocess.check_output("p4 files {}".format(labelsyncName), shell=True, universal_newlines=True).split('\n')
    output = ""
    for i in outputLines:
        if "/{}/".format(DEPOT) in i:
            output = i.strip()
    assert(output),"Could not retrieve latest recommended label for depot "+DEPOT
    #if DEBUG > 4: print ("getRecommendedLabels: output = {}".format(output))
    return output


def printPretty(records,num,title='Summary:'):
    #import pdb; pdb.set_trace()
    if isinstance(records, list):
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

########################################################################
# MAIN
########################################################################
setLithiumP4Env()
PREFIX  = setPrefix()
createWorkspaceDir(PREFIX, DISK)
createP4Client(PREFIX, P4ClientFile)
sourceProjFiles()
getInputFileStruct()##



printPretty(NapierInputStruct,3,"Napier Summary:")
printPretty(HawkeyeInputStruct,3,"Hawkeye Summary:")



import pdb; pdb.set_trace()




print ("\n\n")
for i in records:
    print (i.blockname)
    print ("\t{:35} {:90}\n\t{:35} {:90}".format(
            "napierVerifInfoFile:",i.napierVerifInfoFile, "hawkeyeVerifInfoFile:",i.hawkeyeVerifInfoFile))
    print ("\t{:35} {:90}\n\t{:35} {:90}".format(
            "napierCommonVerifFile:",i.napierCommonVerifFile, "hawkeyeCommonVerifFile:",i.hawkeyeCommonVerifFile))
    print ("\t{:35} {:90}\n\t{:35} {:90}".format(
            "napierDesignFile:",i.napierDesignFile, "hawkeyeDesignFile:",i.hawkeyeDesignFile))








"""
Block  = collections.namedtuple('Block', 'blockname \
napierLabelname napierVerifInfoFile napierCommonVerifFile napierDesignFile \
hawkeyeLabelname hawkeyeVerifInfoFile hawkeyeCommonVerifFile hawkeyeDesignFile')
"""









"""
my $client1 = "$block" . "$prefix" . "1.txt";
my $client2 = "$block" . "$prefix" . "2.txt";
print "\n client1: $client1\n";
print "\n client2: $client2\n";

# Write client to a temp file
$output = `$p4 client -o > "$client1"`;
open $fh, '<', "$client1" or die "Could not open $!\n";
# open the file in write mode and write all lines
# except regress command line
open( FILE, ">", "$client2" );
while ( my $line = <$fh> ) {
    if ( $line =~ m/^$/ || $line =~ m/^#/ ) {

        # Skipping Commented and Empty Lines
        print FILE $line;
        next;
    }
    elsif ( $line =~ m/^View:/ ) {
        $line = <<"END_MESSAGE";
View: 
                                                                                                         
	//depot/prj/qca/$DEPOT/... //$prefix/...
				
END_MESSAGE

    }
    elsif ( $line =~ m/Root:/ ) {
        $line = "Root:  $ENV{'PROJECTS_HOME'}\n";

        #print "\nline:".$line;
    }
    elsif ( $line =~ /^Host:/ ) {
        $line = "";
    }
    elsif ( $line =~ m/\/\// ) {
        next;
    }
    print FILE $line;
}
close(FILE);
close($fh);
$output = `$p4 client -i < "$client2"`;

print "updated the p4 client: $output\n";
if ( -e $client1 ) {
    unlink($client1) or die "$client1: $!";
}
if ( -e $client2 ) {
    unlink($client2) or die "$client2: $!";
}

"""
