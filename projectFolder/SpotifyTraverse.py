from __future__ import print_function
import pyspark
from pyspark import SparkContext, SparkConf
from pyspark.sql import SparkSession
import time
import os,sys
import unicodedata

local = False

if not local:
    master = os.environ["SPARK_MASTER"]
    master = "spark://{}:7077".format(master)
    conf = SparkConf().setAppName("SpotTrawl").setMaster(master)
    spark = SparkContext(conf=conf)
    sqlc = SparkSession.builder\
        .master(master)\
        .appName("SpotTrawl")\
        .config("spark.sql.warehouse.dir", "file:///")\
        .getOrCreate()
    cwd = "file:///projectFolder"
else:
    spark = pyspark.SparkContext("local[*]")
    spark.setLogLevel("OFF")
    from pyspark.sql import SQLContext
    sqlc = SQLContext(spark)
    cwd = os.getcwd()

#===========DATA READING=========
dataSetSize = 1000
print("Importing data from BackupTrawl_{}...".format(dataSetSize))
edges = sqlc.read.parquet("{}/BackupTrawl_{}/trawlEdges.parquet".format(cwd,dataSetSize))
verts = sqlc.read.parquet("{}/BackupTrawl_{}/trawlVerts.parquet".format(cwd,dataSetSize))

#======CREATE VERT DICTIONARY===========
vIDDict = {}
nIDDict = {}
encoding = "utf8"
print("Creating reference dictionary...")
artistList = verts.collect()
for i in artistList:
    nID = i[1].encode(encoding)
    vertID = i[0]
    vIDDict["vertID {}".format(vertID)]={'nID':nID}
    nIDDict["nID {}".format(nID)] = {'rel':[],'nID':nID,'distance':"infinity",'degree':0,'parent':[]}

#======DICTIONARY HELPER FUNCTIONS=========
def getNode(nID):
    return nIDDict.get("nID {}".format(nID))

def getNIDByKey(key):
    return nIDDict.get("{}".format(key))['nID']   

def getnID(vertID):
    return vIDDict.get("vertID {}".format(vertID))['nID']

def setRel(nID,B):
    nIDDict.get("nID {}".format(nID))['rel'] = B   
 

def setParent(nID,parent):
    nIDDict.get("nID {}".format(nID))['parent'] = parent 

def setDist(nID,distance):
    nIDDict.get("nID {}".format(nID))['distance'] = distance 


def getDist(nID):
    return nIDDict.get("nID {}".format(nID))['distance'] 

#======DATA FORMATTING 1==============
print("Formatting data, round 1...")
edges = edges.rdd.map(lambda x: (getnID(x[0]),getnID(x[1])))
edges = edges.reduceByKey(lambda x,y: x + "_as_well_as_" + y)
edges = edges.map(lambda x: (x[0],x[1].split("_as_well_as_")))

#======CREATE GRAPH==================
print("Creating graph...(this'll take a bit)")
for artist in edges.collect():    
    setRel(artist[0],artist[1])

#======DATA FORMATTING 1==============
print("Formatting data, round 2...")
artRef = verts.rdd.map(lambda x: (x[1].split(" _ _ ")[0],x[1]))
artRef = sqlc.createDataFrame(artRef,['name','nID'])

#======TRAVERSAL=====================
def clean():
    for key,value in nIDDict.items():
        keyNID = getNIDByKey(key)
        setParent(keyNID,[])
        setDist(keyNID,"infinity")

def traverse(orig):
    clean()
    Q =[orig]
    getNode(Q[0])['distance']=0
    runningSum = 0.0
    maxDist = 0
    numNodes = 0.0
    while Q:
        current = getNode(Q[0])
        Q = Q[1:len(Q)]
        for i in current['rel']:
            if getDist(i) == "infinity":
                distTo = current['distance']+1
                setDist(i,distTo)
                setParent(i,current)
                numNodes+=1
                runningSum+=distTo
                if distTo > maxDist:
                    maxDist = distTo
                Q.append(i)
    if numNodes>=int(dataSetSize):
        return (int(maxDist),float(runningSum/numNodes))
    else:
        return (int(dataSetSize),float(dataSetSize))

#========GRAPH ANALYSIS====================
print("Finding eccentricities...")
artistRDD = spark.parallelize(artistList,800)
avePathLen = artistRDD.map(lambda x: (x[1].split(" _ _ ")[0],traverse(x[1].encode(encoding))))
avePathLen = avePathLen.map(lambda x: (unicodedata.normalize('NFKD',x[0]).encode("ascii","ignore"),x[1][0],x[1][1]))
avePathLen = sqlc.createDataFrame(avePathLen,["Artist","MaxPathLen","AvePathLen"])
avePathLen = avePathLen.orderBy("AvePathLen",ascending=True)

#=======DISPLAY RESULTS====================
print("BEGIN DESIRED OUTPUT")
avePathLen.show(1000)
print("END DESIRED OUTPUT")