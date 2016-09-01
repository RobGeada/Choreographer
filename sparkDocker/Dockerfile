#Generated 2016-09-01 15:01:21.455551
#This generated Dockerfile is based off of Matthew Farrellee's openshift-spark Dockerfile

FROM centos:latest

MAINTAINER Rob Geada

RUN yum install -y epel-release tar java && \
    yum clean all

RUN cd /opt && \
    curl https://dist.apache.org/repos/dist/release/spark/spark-2.0.0/spark-2.0.0-bin-hadoop2.7.tgz | \
        tar -zx && \
    ln -s spark-2.0.0-bin-hadoop2.7 spark
RUN yum install -y nss_wrapper && yum clean all

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

RUN mkdir /projectFolder
COPY ./projectFolder /projectFolder
RUN chmod -R +rx /projectFolder

# Switch to the user 185 for OpenShift usage
USER 185

# Start the main process
CMD ["/opt/spark/bin/launch.sh"]