import subprocess
import os,sys,shutil
import string
import random
import time
import datetime

from generateDockerfile import generateDockerfile
import healthManager as health

#======PARSE COMMAND LINE ARGUMENTS====================
args = sys.argv
projectName,launcherName,scaleTo = None,None,None
for i,arg in enumerate(args):
	if arg == "-h":
		helpString = """
	-w: Specify the number of worker nodes desired in your cluster
	-l: Specify the name of the program in the projectFolder that defines your app launcher
	-p: Specify the name of your project for OpenShift purposes
	-h: Print this help
		"""
		print helpString
		sys.exit()
	if arg == "-p":
		projectName = args[i+1].lower()
	if arg == "-l":
		launcherName= args[i+1]
	if arg == "-w":
		scaleTo= int(args[i+1])	


#+=====GET USER PARAMETERS IF NO CL ARGUMENTS===========
if projectName == None:
	projectName = raw_input("Set project name: ").lower()
if launcherName== None:
	launcherName = raw_input("Set program name: ")
if scaleTo==None:
	valid = False
	while not valid:
		try:
			scaleTo = int(raw_input("How many workers desired? "))
			valid = True
		except ValueError:
			print "Input must be integer!"

if scaleTo > 10:
	raw_input("It looks like you're trying to make a very large cluster. Check with your cluster admin before proceeding. ")
	sys.exit()

#======DEFINE POD NAMES=================================
dockerName = projectName
projectName += "-"+random.choice(string.ascii_lowercase)+random.choice(string.ascii_lowercase)

#======CREATE PROJECT, WORKER/DRIVER DOCKERFILES,INITIAL CLUSTER==================
shutil.copytree("projectFolder", "sparkDocker/projectFolder")
os.system("cd sparkDocker;python makeClusterDocker.py")
bashCommand = "oc new-project {};cd sparkDocker;make create".format(projectName)
os.system(bashCommand)
shutil.rmtree("./sparkDocker/projectFolder")

#=======GET WORKER AND MASTER DEPLOYMENT NAMES==========
p = subprocess.Popen(['oc', 'get', 'rc'], stdout=subprocess.PIPE, stderr=subprocess.PIPE)
out, err = p.communicate()
masterName = None

#determine master and worker names
for word in out.split():
	if "spark-master" in word:
		#save master name for use with driver application
		masterName = word[:-2]
	if "spark-worker" in word: 
		workerName = word

#==============GENERATE DRIVER DOCKERFILE===============
if masterName!=None:
	generateDockerfile(masterName,launcherName)
else:
	print "No master node detected!"
	sys.exit()

#==============CREATE DRIVER IMAGE===============
appName = "rgeada/{}".format(dockerName)
os.system("docker build -t {} .".format(appName))
os.system("docker push {}".format(appName))


#==============CLUSTER READINESS CHECKS===============
os.system('clear')
print("Beginning Cluster Management Interface...\n")

#wait for initial cluster to ready-up
print("Waiting for initial cluster deployment to become ready...")
while not health.clusterOperational(3):
	time.sleep(1)

#scale cluster and wait for completion
print "\n\nScaling cluster to desired size..."
os.system("oc scale --replicas={} rc {}".format(scaleTo,workerName))
tries = 0
clusterTgt = scaleTo
while not health.clusterOperational(clusterTgt):
	time.sleep(1)
	tries+=1
	if tries > 100:
		print(" Desired cluster size cannot initialize, lowering target...")
		clusterTgt-=1
		os.system("oc scale --replicas={} rc {}".format(clusterTgt,workerName))

#deploy application, clear program logs
print("\n\nDeploying application...")
os.system("oc new-app {}".format(appName))

#wait for driver to become ready
print("\n\nWaiting on driver pod to become ready...")
while not health.driverOperational(dockerName):
	time.sleep(1)

#format logs for data retrieval
f=open("programLogs","w")
f.write("Deployment began at {}".format(datetime.datetime.now()))
f.close()

#===========DRIVER RESULTS OBSERVATION===========
os.system("clear")
print("Beginning driver pod observation at {}...\n".format(datetime.datetime.now()))
while not health.getLogs(dockerName):
	time.sleep(1)

os.system("oc delete project/{}".format(projectName))
print("Application has finished! View logs at {}/programLogs".format(os.getcwd()))