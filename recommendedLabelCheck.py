#!/pkg/qct/software/python/3.5.2/bin/python
import sys, os, getopt                                            
from pathlib import Path                                          
import json                                                       
import subprocess
import re
os.environ['PATH'] += (os.pathsep + '/pkg/qct/software/p4')
os.putenv('P4PORT', "p2.qca.qualcomm.com:1666")
SCRIPT_ROOT            = '/usr2/c_ckebri/pythonScripts'           
myJsonFile             = Path(SCRIPT_ROOT) / 'input' / 'JsonObjCollection.json'
assert(myJsonFile.is_file()),"Error: File '{}' does not exist".format(myJsonFile)
with myJsonFile.open() as data_file:
    myJsonData = json.load(data_file)
    data_file.close()

PROJECTS    = ('P4Labels_HAWKEYE','P4Labels_NAPIER')
PROJECT     = ""
blockList   = list()

#================================================================================================================================

def getRecommendedLabels(blockname,labelsyncName):
    global blockList
    output = subprocess.check_output("p4 files {}".format(labelsyncName), shell=True, universal_newlines=True).strip()
    print ("\n\tgetRecommendedLabels: output for {}\n".format(blockname),output)
    if 'NAPIER' in PROJECT:
        if ( len(output.split('\n')) > 2 ) or (not re.search("napier",output, re.I)):
            blockList.append(blockname)
    elif 'HAWKEYE' in PROJECT:
        if ( len(output.split('\n')) > 2 ) or (re.search("napier",output, re.I)):
            blockList.append(blockname)
    else: raise SystemExit("Script Error")
#================================================================================================================================

for prj in PROJECTS:
    PROJECT = prj
    #blockList.clear()
    print ("\n\n\tPROJECT:",prj)
    for i in myJsonData[PROJECT]:                                                                                                                           
        getRecommendedLabels(i,myJsonData[PROJECT][i])

print ("\n\n",blockList)
#for i in blockList:
#    print ("p4 files", myJsonData[PROJECT][i])


