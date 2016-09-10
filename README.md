# Choreographer

This tool creates an interface by which to dynamically generate Spark clusters on OpenShift for deployment of PySpark applications. The interface deals with cluster creation, managing cluster health and status, and application deployment when the cluster is ready. Once your app has finished and produced its desired output, Choreographer will grab the output, write it to the programLogs file, and then shutdown the cluster, thus cleaning up after itself.

###Prequisites
* Docker version 1.9.1
* Python 2.7
* [OpenShift Origin](https://github.com/openshift/origin/releases/tag/v1.3.0-alpha.3)

That's it!

###Installation
Run the following in your install directory of choice:
```
git clone https://github.com/RobGeada/Choreographer.git
cd Choreographer
chmod +x choreograph 
export PATH=$PATH:$(pwd)
```

###Program Configuration
In order for the OpenShift nodes to properly communicate with your PySpark app, a few parameters must be properly set inside your app code.

1. Your Spark master address should be as follows: `master = "spark://{}:7077".format(os.environ["SPARK_MASTER"]`
2. The spark warehouse directory should be set to: `file:///`
3. Your application launcher and its working directory must be inside projectFolder
4. To specify the desired output of your program, include the following:
```
print program output etc...
print("DESIRED OUTPUT LENGTH: 1000")
time.sleep(500)
```
This will extract the previous 1000 lines of log output and write them to your local disk. Additionally, I recommend including a sleep counter after the desired input; this ensures that your driver pod will remain running for a bit after output generation, thus ensuring that Choreographer has time to grab the results. 

###Setup
1. Ensure your Spark app meets the configuration guidelines as specified above.
2. Create a project directory for your Spark application. 
3. Create a directory named "app" within the project directory. This should contain your app code and all necessary datasets.
3. Edit the prereqs file within the app folder as neccesary. The file contains instructions on how to properly format your prereq list.

For further reference, the apps in the [Choreographer-Demos](https://github.com/RobGeada/Choreographer-Demos) repo meet all of the setup and configuration guidelines described above.

###Dockerfile Generation
Choreographer will generate Dockerfiles for the worker, master, and driver nodes as per your program's specifications. These generated Dockerfiles are based off of RAD Analytics' [openshift-spark](https://github.com/radanalyticsio/openshift-spark) repo.


###Usage
The aim of this project was to create an "easy button" interface for the deployment of PySpark apps. As such, a cluster can be created, an application deployed, and results collected all from a single command. Use the launchProject.py program to do so, and use the following flags to set cluster specificiations.
```
        -w,     --workers: Specify the number of worker nodes desired in your cluster
	    -l,    --launcher: Specify the name of the program in the app that defines your app launcher
	    -c, --clusterCred: Specify your cluster credentials (username:pass)
	    -n,  --newCluster: Create new cluster, rather than use existing one.
	    -h,        --help: Print this help
```
So to deploy the example SpotifyTraverse application included with this repo, use the following command:

`choreograph -w 10 -l SpotifyTraverse.py -o developer:developer`

It's important to remember that Choreographer creates clusters custom built for your application, so use --newCluster in any situation where any part of your project (except for the driver program) has changed.
