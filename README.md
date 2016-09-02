# OpenShift-Deploy

This tool creates an interface by which to dynamically generate Spark clusters on OpenShift for deployment of PySpark applications. The interface deals with cluster creation, managing cluster health and status, and application deployment when the cluster is ready. Once your app has finished and produced its desired output, OpenShift-Deploy will grab the output, write it to the programLogs file, and then shutdown the cluster, thus cleaning up after itself.

###Program Configuration
In order for the OpenShift nodes to properly communicate with your PySpark app, a few parameters must be properly set inside your app code.

1. Your Spark master address should be as follows: `master = "spark://{}:7077".format(os.environ["SPARK_MASTER"]`
2. The spark warehouse directory should be set to: `file:///`
3. Your application launcher and its working directory must be inside projectFolder
4. To specify the desired output of your program, include the following:
```
print program output etc...
print("DESIRED OUTPUT LENGTH: 1000")
```
This will extract the previous 1000 lines of log output and write them to your local disk.

For further reference, the [SpotifyTraverse.py](https://github.com/RobGeada/OpenShift-Deploy/blob/master/projectFolder/SpotifyTraverse.py) code has all of the specifications above.

###Setup
1. Ensure your program meets the configuration guidelines as specified above.
2. Fill the projectFolder directory with your app code and whatever support files it needs to run. For reference, I've included my [SpotifyTraverse](https://github.com/RobGeada/SpotifyTraverse) app.
3. Edit the prereqs file as neccesary. The file contains instructions on how to properly format your prereq list.
4. Use `oc login` to login to an OpenShift cluster.

###Dockerfile Generation
OpenShift-Deploy will generate Dockerfiles for the worker, master, and driver nodes as per your program's specifications. These generated Dockerfiles are based off of RAD Analytics's [openshift-spark](https://github.com/radanalyticsio/openshift-spark) repo.


###Usage
The aim of this project was to create an "easy button" interface for the deployment of PySpark apps. As such, a cluster can be created, an application deployed, and results collected all from a single command. Use the launchProject.py program to do so, and use the following flags to set cluster specificiations.
```
    -w,    --workers: Specify the number of worker nodes desired in your cluster
	-l,   --launcher: Specify the name of the program in the projectFolder that defines your app launcher
	-p,    --project: Specify the name of your project for OpenShift purposes
	-n, --newCluster: Create new cluster, rather than using existing one.
 	-h,       --help: Print this help
```
So to deploy the example SpotifyTraverse application included with this repo, use the following command:

`python launchProject.py -w 10 -l SpotifyTraverse.py -p spottrawl`

It's important to remember the OpenShift-Deploy creates clusters custom built for your application, so use --newCluster in any situation where any part of your project (except for the driver program) has changed.
