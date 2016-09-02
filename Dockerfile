#Generated 2016-09-02 10:56:16.164549
#This generated Dockerfile is based off of Matthew Farrellee's openshift-spark Dockerfile

FROM centos:latest

MAINTAINER Rob Geada 

RUN yum install -y epel-release tar java && \
    cd /opt && \
    curl https://dist.apache.org/repos/dist/release/spark/spark-2.0.0/spark-2.0.0-bin-hadoop2.7.tgz | \
    tar -zx && \
    ln -s spark-2.0.0-bin-hadoop2.7 spark && \
    yum install -y nss_wrapper python python-pip && yum clean all

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
RUN mkdir projectFolder
COPY ./projectFolder /projectFolder
RUN chmod -R +rx /projectFolder
USER 185

ENV SPARK_MASTER=spark-master-rw03 \ 
    SPARK_USER=test \ 
    PYTHONIOENCODIG=utf_8 \ 
    LAUNCH_PROGRAM=SpotifyTraverse.py

CMD ["/opt/spark/bin/launch.sh"]