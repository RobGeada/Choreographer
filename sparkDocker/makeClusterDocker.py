import datetime

'''
Based on the contents of the prereqs file in the projectFolder, this will
generate a Dockerfile to serve as the worker and master pod in OpenShift deployment
'''

prereqPackages = []
with open("./app/prereqs") as f:
	for line in f:
		prereqPackages.append(line)

dockerTemplate = "#Generated {}\n".format(datetime.datetime.now())
dockerTemplate +="#This generated Dockerfile is based off of Matthew Farrellee's openshift-spark Dockerfile\n\n"

dockerTemplate +=\
r"""FROM centos:latest

MAINTAINER Rob Geada

RUN yum install -y epel-release tar java && \
    yum clean all

RUN cd /opt && \
    curl https://dist.apache.org/repos/dist/release/spark/spark-2.0.0/spark-2.0.0-bin-hadoop2.7.tgz | \
        tar -zx && \
    ln -s spark-2.0.0-bin-hadoop2.7 spark
RUN yum install -y nss_wrapper """

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
    PYTHONIOENCODIG=utf_8

# Add scripts used to configure the image
COPY scripts /tmp/scripts

# Custom scripts
USER root
RUN [ "bash", "-x", "/tmp/scripts/spark/install" ]

# Cleanup the scripts directory
USER root
RUN rm -rf /tmp/scripts

RUN mkdir /app
COPY ./app /app
RUN chmod -R +rx /app

# Switch to the user 185 for OpenShift usage
USER 185

# Start the main process
CMD ["/opt/spark/bin/launch.sh"]"""

f = open('Dockerfile','w')
f.write(dockerTemplate)
f.close()
