from __future__ import print_function
import os,sys
import subprocess
import time
import datetime

#===========GET POD INFO==================================
#Prints out a list of the running master, worker, and driver pods
def getPodInfo(printPods=True):
	#query cluster for pods
	p = subprocess.Popen(['oc', 'get', 'pods'], stdout=subprocess.PIPE, stderr=subprocess.PIPE)
	out, err = p.communicate()
	masterName = None

	#initialize lists for query parsing
	rawPodList = out.split()
	podList=[]

	#parse query output, keep relevant columns
	for i,info in enumerate(rawPodList):
		if (i%5 != 0):
			continue
		elif info=="NAME":
			continue
		else:
			if rawPodList[i+4][-1:]=="s":
				age = 0
			else:
				age = int(rawPodList[i+4][:-1])
			podList.append({"name":rawPodList[i],"status":rawPodList[i+2],"age":age})

	#print out a list of pods to the terminal
	if printPods:
		os.system('clear')
		print("Beginning cluster health manager...\n")
		print("NAME\t\t\t\tAGE\tSTATUS")
		for pod in podList:
			if pod['status']!="Terminating" and pod['name'][-6:]!="deploy":
				spacer = " "*(32-len(pod['name']))
				print("{}{}{} m\t{}".format(pod['name'],spacer,pod['age'],pod['status']))

	return podList 

#===========CLUSTER OPERATIONAL==================================
#Returns true if the number of worker nodes us equivalent to the target size, and master is running
def clusterOperational(tgtSize):
	podList = getPodInfo(printPods=False)

	#parse podlist for running or creating workers
	numOperational = 0
	for pod in podList:
		if pod['status']=="ContainerCreating" and pod['age']>=1:
			print("\n")
			os.system("oc delete pod/{}".format(pod['name']))		
		if "master" in pod['name'] and pod['status']=="ContainerCreating":
			numOperational=0
			break
		elif "worker" in pod['name'] and "deploy" not in pod['name']:
			if pod['status']=="Running":
				numOperational += 1

	#display results to terminal, flush stdout for cleanliness
	print("\rCluster Status: {} of {} worker nodes operational.".format(numOperational,tgtSize),end="")
	sys.stdout.flush()
	
	#return true if cluster is up and running
	if numOperational==tgtSize:
		return True
	else:
		return False

#===========DRIVER OPERATIONAL==================================
#Returns true if the driver pod is running
def driverOperational(driverName):
	podList = getPodInfo(printPods=False)
	#parse podlist for driver
	for pod in podList:
		if driverName in pod['name']:
			if pod['status']=="ContainerCreating" and pod['age']>=3:
				os.system("oc delete pod/{}".format(pod['name']))
			elif driverName in pod['name'] and "deploy" not in pod['name'] and pod['status']=="Running":
				return True
	return False

#===========GET LODS==================================
#Parses driver logs for specific output, saves that to log file
#This ensures you get the desired results without creating massive files
def getLogs(dockerName):
	podList = getPodInfo(printPods=False)

	#get master,worker,and driver deployment configs 
	driverName,masterName,workerName = None,None,None
	driverUp,masterUp,numWorkers = "STALLED","STALLED",0

	for pod in podList:
		if dockerName in pod['name'] and 'deploy' not in pod['name'] and pod['status']=="Running":
			driverUp = "RUNNING"
			driverName = pod['name']
		if "spark-master" in pod['name'] and pod['status']=="Running":
			masterUp = "RUNNING"
			masterName = pod['name'][:-8]
		if "spark-worker" in pod['name'] and pod['status']=="Running":
			numWorkers += 1
			workerName = pod['name'][:-8]
	
	#display results
	outString = "\r| Master: {} | ".format(masterUp)+\
				"Driver: {} | ".format(driverUp)+\
				"Workers: {} | ".format(numWorkers)+\
				"Results..."
	print(outString,end="")

	#if the driver is running, get the logs
	if driverName != None:
		p = subprocess.Popen(['oc', 'logs','{}'.format(driverName)], stdout=subprocess.PIPE, stderr=subprocess.PIPE)
		out, err = p.communicate()
		
		#find desired output in log file
		tgtOutStart = out.find("BEGIN DESIRED OUTPUT")
		tgtOutEnd = out.find("END DESIRED OUTPUT")

		#if the desired output is found, extract and write it
		if tgtOutStart != -1 and tgtOutEnd != -1:
			f = open("programLogs","a")
			f.write("\n\n=============LOGS RETRIEVED AT {}=============\n\n".format(datetime.datetime.now()))
			f.write(out[tgtOutStart:tgtOutEnd+18])
			f.close()

			#shuttdown cluster upon success
			print("FOUND |            ",end="")
			os.system("oc delete dc/{}".format(dockerName))
			os.system("oc delete dc/{}".format(masterName))
			os.system("oc delete dc/{}".format(workerName))
			return True
		else:
			print("NOT YET FOUND |      ",end="")
	sys.stdout.flush()
	return False