import subprocess
import os,sys,shutil
import string
import random
import time
import datetime

from generateDockerfile import generateDockerfile
import healthManager as health

try:
	from notifyMe import notifyMe
	notifyMeEnabled = True
except ImportError:
	notifyMeEnabled = False
	pass

#======PARSE COMMAND LINE ARGUMENTS====================
args = sys.argv
projectName,launcherName,scaleTo,newCluster = None,None,None,False
for i,arg in enumerate(args):
	if arg == "-h"  or arg == "--help":
		helpString = """
	-w,     --workers: Specify the number of worker nodes desired in your cluster
	-l,    --launcher: Specify the name of the program in the projectFolder that defines your app launcher
	-p,     --project: Specify the name of your project for OpenShift purposes
	-d,  --dockerName: Specify your Docker Hub username
	-o, --clusterCred: Specify your cluster credentials (username:pass)
	-n,  --newCluster: Create new cluster, rather than use existing one.
 	-h,        --help: Print this help
		"""
		print helpString
		sys.exit()
	if arg == "-p" or arg == "--project":
		projectName = args[i+1].lower()
	if arg == "-d" or arg == "--dockerName":
		dockerUsername = args[i+1]
	if arg == "-o" or arg == "--clusterCred":
		clusterUser,clusterPass = args[i+1].split(":")
	if arg == "-l"  or arg == "--launcher":
		launcherName= args[i+1]
	if arg == "-w"  or arg == "--workers":
		scaleTo= int(args[i+1])
	if arg == "-n"  or arg == "--newCluster":
		newCluster = True

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

def deployCluster():
	#======CREATE PROJECT, WORKER/DRIVER DOCKERFILES,INITIAL CLUSTER==================
	shutil.copytree("projectFolder", "sparkDocker/projectFolder")
	os.system("cd sparkDocker;python makeClusterDocker.py")
	bashCommand = "oc new-project {};cd sparkDocker;make create".format(projectName)
	os.system(bashCommand)
	shutil.rmtree("./sparkDocker/projectFolder")

	#=======GET WORKER AND MASTER DEPLOYMENT NAMES==========
	masterName,workerName,driverName = health.getDCInfo()

	#==============BUILD DRIVER ==========================
	buildNewDriver(masterName)

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


#=============DEPLOY DRIVER PODS==========================
def deployApp():
	#=======BUILD DRIVER IMAGE==========
	masterName,workerName,driverName = health.getDCInfo()
	appName = buildNewDriver(masterName)

	#==============DEPLOY DRIVER IMAGE===============
	if driverName == None:
		print("\n\nDeploying application...")
		os.system("oc new-app {}".format(appName))
	else:
		health.deleteDriver()
		print("\nRedeploying new application...\n")
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
	tries = 0
	while not health.getLogs(dockerName):
		tries+=1
		time.sleep(5)
		if tries > 3600:
			os.system("oc login -u {} -p {}".format(clusterUser,clusterPass))
			tries = 0

	#===========CLEANUP=======================	
	print("\nApplication has finished! View logs at {}/programLogs".format(os.getcwd()))
	if notifyMeEnabled:
		notifyMe("Deployment has finished!","{}/programLogs".format(os.getcwd()))
	#choice = "d"
	choice = raw_input("Would you like to destroy the {} cluster (d) or leave it running driverless (r)? ".format(dockerName))
	print("\n")
	if choice == "r":
		health.cleanUp("Driver")
		print("\nDriver has been removed. Using Choreographer again will result in the deployment of a new driver.")
	else:
		health.cleanUp("All")
		print("\nCluster has been removed. Using Choreographer again will result in the creation of a new cluster.")

#============CREATE NEW DRIVER IMAGE==================
def buildNewDriver(masterName):
	#generate new docker image
	if masterName!=None:
		generateDockerfile(masterName,launcherName)
	else:
		print "No master node detected!"
		sys.exit()

	#build and push driver image
	appName = "{}/{}".format(dockerUser,dockerName)
	os.system("docker build -t {} .".format(appName))
	os.system("docker push {}".format(appName))
	return appName

#==============MAIN===============
if newCluster:
	deployCluster()
	deployApp()
else:	
	masterName = health.getDCInfo()[0]
	if masterName==None:
		deployCluster()
		deployApp()
	else:
		deployApp()