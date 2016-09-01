# OpenShift-Deploy

This tool creates an interface by which to dynamically generate Spark clusters on OpenShift for deployment of PySpark applications. The interface deals with managing cluster health and status, and deploys your app when the cluster is ready to receive it. Once your app has finished and produced it's desired output, OpenShift-Deploy will grab the output and write it to a file, then shutdown the cluster, cleaning up after itself.

###Program Configuration
In order for the OpenShift nodes to properly communicate with your PySpark app, a few parameters must be properly set inside your app code.
1. Your Spark master address should be as follows: 

`master = "spark://{}:7077".format(os.environ["SPARK_MASTER"]`
2. The spark warehouse directory should be set as `file:///`
3. Your application launcher and it's working directory must be inside projectFolder
4. To specify the desired output of your program, bracket the desired output with the following:
```
print("BEGIN DESIRED OUTPUT")
output etc...
print("END DESIRED OUTPUT")
```

###Setup
1. Ensure your program meets the configuration guidelines as specified above.
2. Fill the projectFolder directory with your app code and whatever support files it needs to run. For reference, I've included my [SpotifyTraverse](https://github.com/RobGeada/SpotifyTraverse) app.
3. Edit the prereqs file as neccesary. The file contains instructions on how to properly format your prereq list.
4. Use `oc login` to login to an OpenShift cluster.

###Usage
The aim of this project was to create an "easy button" interface for the deployment of PySpark apps. As such, a cluster can be created, an application deployed, and results collected all from a single command. Use the launchProject program to do so, and use the following flags to set cluster specificiations.
```
  -w: Specify the number of worker nodes desired in your cluster
  -l: Specify the name of the program in the projectFolder that defines your app launcher
  -p: Specify the name of your project for OpenShift purposes
  -h: Print this help
```
So to deploy the example SpotifyTraverse application included with this repo, use the following command:
`python launchProject -w 10 -l SpotifyTraverse.py -p spottrawl
