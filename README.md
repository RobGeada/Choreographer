# OpenShift-Deploy

This tool creates an interface by which to dynamically generate OpenShift clusters for deployment of PySpark applications. The interface deals with managing cluster health and status, and deploys your app when the cluster is ready to receive it. Once your app has finished and produced it's desired output, OpenShift-Deploy will grab the output and write it to a file, then shutdown the cluster, cleaning up after itself.

###Setup
1. Fill the projectFolder directory with your app code and whatever support files it needs to run. For reference, I've included my [SpotifyTraverse](https://github.com/RobGeada/SpotifyTraverse) app.
2. Edit the prereqs file as neccesary. The file contains instructions on how to properly format your prereq list.

###Usage
The aim of this project was to create an "easy button" interface for the deployment of PySpark apps. As such, a cluster can be created, an application deployed, and results collected all from a single command. Use the launchProject.py program
