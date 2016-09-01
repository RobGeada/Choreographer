# OpenShift-Deploy

This tool creates an interface by which to dynamically generate OpenShift clusters for deployment of PySpark applications. The interface deals with managing cluster health and status, and deploys your app when the cluster is ready to receive it. Once your app has finished and produced it's desired output, OpenShift-Deploy will grab the output and write it to a file, then shutdown the cluster, cleaning up after itself.

###Usage
