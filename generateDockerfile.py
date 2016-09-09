import datetime,os,sys

'''
Based on the contents of the prereqs file in the projectFolder, this will
generate a Dockerfile to serve as the driver pod in OpenShift deployment.
'''

def generateDockerfile(masterName,launchProgram):
	os.chdir(sys.path[0])
	prereqPackages = []
	with open("app/prereqs") as f:
		for line in f:
			prereqPackages.append(line)

	dockerTemplate = "#Generated {}\n".format(datetime.datetime.now())
	dockerTemplate +="#This generated Dockerfile is based off of Matthew Farrellee's openshift-spark Dockerfile\n\n"

	dockerTemplate+=\
	r"""FROM centos:latest

MAINTAINER Rob Geada 

RUN yum install -y epel-release tar java && \
    cd /opt && \
    curl https://dist.apache.org/repos/dist/release/spark/spark-2.0.0/spark-2.0.0-bin-hadoop2.7.tgz | \
    tar -zx && \
    ln -s spark-2.0.0-bin-hadoop2.7 spark && \
    yum install -y nss_wrapper python python-pip """

	yumPackages = []
	pipPackages = []
	for line in prereqPackages:
		if line[0]=="#" or line[0]=="\n":
			continue
		pkg,flag = line.split(" ")[0],line.split(" ")[1].replace("\n","")
		onlyYums = True
		if flag == "-y":
			yumPackages.append(pkg)			
		elif flag == "-p":
			pipPackages.append(pkg)
	for pkg in yumPackages:	
		dockerTemplate+= "{} ".format(pkg)
	for pkg in pipPackages:
		dockerTemplate+= "&& pip install {} ".format(pkg)

	dockerTemplate+=\
r"""&& yum clean all

ENV PATH=$PATH:/opt/spark/bin \
 	SPARK_HOME=/opt/spark \
 	PYTHONPATH=$SPARK_HOME/python:$PYTHONPATH \
    PYTHONPATH=$SPARK_HOME/python/lib/py4j-0.10.1-src.zip:$PYTHONPATH

# Add scripts used to configure the image
COPY scripts /tmp/scripts

# Custom scripts
USER root
RUN [ "bash", "-x", "/tmp/scripts/spark/install" ]

# Cleanup the scripts directory
USER root
RUN rm -rf /tmp/scripts

# Switch to the user 185 for OpenShift usage
COPY ./app /app
RUN chmod -R +rx /app
USER 185
"""
# Start the main process"""

   	dockerTemplate+="\nENV SPARK_MASTER={} \ ".format(masterName)
   	dockerTemplate+="\n    SPARK_USER=test \ "
   	dockerTemplate+="\n    PYTHONIOENCODIG=utf_8 \ "
   	dockerTemplate+="\n    LAUNCH_PROGRAM={}".format(launchProgram)
   	dockerTemplate+='\n\nCMD ["/opt/spark/bin/launch.sh"]'

	f = open('Dockerfile','w')
	f.write(dockerTemplate)
	f.close()

if __name__ == "__main__":
	generateDockerfile("test","test.py")