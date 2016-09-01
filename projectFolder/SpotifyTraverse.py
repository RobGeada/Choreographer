from __future__ import print_function
import pyspark
from pyspark import SparkContext, SparkConf
from pyspark.sql import SparkSession
import time
from pyspark.sql import Row
import os,sys
import shutil
import json
import unicodedata

local = False

if not local:
    master = os.environ["SPARK_MASTER"]
    master = "spark://{}:7077".format(master)
    conf = SparkConf().setAppName("SQLeleton").setMaster(master)
    spark = SparkContext(conf=conf)
    sqlc = SparkSession.builder\
        .master(master)\
        .appName("SQLeleton")\
        .config("spark.sql.warehouse.dir", "file:///")\
        .getOrCreate()
    from pyspark.sql.functions import avg
    cwd = "file:///projectFolder"
else:
    spark = pyspark.SparkContext("local[*]")
    spark.setLogLevel("OFF")
    from pyspark.sql import SQLContext
    sqlc = SQLContext(spark)
    from pyspark.sql import SQLContext
    from pyspark.sql.functions import avg
    cwd = os.getcwd()

#===========PROGRAM FLOW HELPERS==========
def wait(label):
    raw_input("waiting for user input at {}".format(label))

def printTitle():
    os.system('clear')
    print("==========================================================================")
    print("Welcome to")   
    print("   _____             _   _  __         _______                 _           ")
    print("  / ____|           | | (_)/ _|       |__   __|               | |          ")
    print(" | (___  _ __   ___ | |_ _| |_ _   _     | |_ __ __ ___      _| | ___ _ __ ")
    print("  \___ \| '_ \ / _ \| __| |  _| | | |    | | '__/ _` \ \ /\ / / |/ _ \ '__|")
    print("  ____) | |_) | (_) | |_| | | | |_| |    | | | | (_| |\ V  V /| |  __/ |   ")
    print(" |_____/| .__/ \___/ \__|_|_|  \__, |    |_|_|  \__,_| \_/\_/ |_|\___|_|   ")
    print("        | |                     __/ |                                      ")
    print("        |_|                    |___/                                       ")
    print("==============Version 1.2=========================8/24/2016===============\n")

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

def getRel(nID):
    return nIDDict.get("nID {}".format(nID))['rel']   

def printNode(nID):
    print("{} is related to {}".format(nID,getRel(nID)))

def setParent(nID,parent):
    nIDDict.get("nID {}".format(nID))['parent'] = parent 

def setDist(nID,distance):
    nIDDict.get("nID {}".format(nID))['distance'] = distance 

def getParent(nID):
    return nIDDict.get("nID {}".format(nID))['parent'] 

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


def parse(dest,mode="Reader"):
    path = getNode(dest)
    result = [path['nID']]
    next = getParent(path['nID'])
    while (next != []):
        result.append(next['nID'])
        next = next['parent']
    result.reverse()

    if len(result)==1:
        print("No connection!")
    else:
        if mode=="Reader":
            print("\nThe shortest path ({} clicks) is:".format(len(result)-1)) 
            for i in result:
                if i != result[-1]:
                    #name = i.encode("utf8")
                    name = i.split(" _ _ ")[0]
                    print("{} -> ".format(name),end="")
                else:
                    #name = i.encode("utf8")
                    name = i.split(" _ _ ")[0]
                    print("{}".format(name))
        else:
            playlistName = result[0].split(" _ _ ")[0] + " to " + result[-1].split(" _ _ ")[0] +\
            " ({}) : ".format(dataSetSize)
            path = []
            for i in result:
                path.append(i)
            print(path)
            API.makePlaylist(playlistName,path)


if 1:
    print("Finding eccentricities...")
    artistRDD = spark.parallelize(artistList,4000)
    avePathLen = artistRDD.map(lambda x: (x[1].split(" _ _ ")[0],traverse(x[1].encode(encoding))))
    avePathLen = avePathLen.map(lambda x: (unicodedata.normalize('NFKD',x[0]).encode("ascii","ignore"),x[1][0],x[1][1]))
    avePathLen = sqlc.createDataFrame(avePathLen,["Artist","MaxPathLen","AvePathLen"])
    avePathLen = avePathLen.orderBy("AvePathLen",ascending=True)
    print("BEGIN DESIRED OUTPUT")
    avePathLen.show(1000)
    print("END DESIRED OUTPUT")
    sys.exit()

#=========UI helpers=============
def lookupOrig():
    content = False
    print("Welcome to the nID lookup interface!\n")
    while not content:
        sqlc.registerDataFrameAsTable(artRef,"artistTable")
        searchTerm = raw_input("Selecting Origin: Who would you like to search for? ")
        print("Searching...")
        searched = sqlc.sql("SELECT nID FROM artistTable WHERE name LIKE '%{}%'".format(searchTerm))
        results = searched.take(16)
        print("\nSearch complete! Our best guesses: ")
        n = 0
        for i in results:
            print("{}: {}".format(n,i[0].encode("utf8")))
            n+=1
        branch = raw_input("Select nID (0-15) or search again (a): ")
        try: 
            branch = int(branch)
            orig = results[branch][0]
            content = True
        except ValueError:
            continue
    return orig
def lookupDest():
    content=False
    while not content:
        sqlc.registerDataFrameAsTable(artRef,"artistTable")
        searchTerm = raw_input("\nSelecting Destination: Who would you like to search for? ")
        print("Searching...")
        searched = sqlc.sql("SELECT nID FROM artistTable WHERE name LIKE '%{}%'".format(searchTerm))
        results = searched.take(16)
        print("\nSearch complete! Our best guesses: ")
        n = 0
        for i in results:
            print("{}: {}".format(n,i[0].encode("utf8")))
            n+=1
        branch = raw_input("Select nID (0-15) or search again (a): ")
        try: 
            branch = int(branch)
            dest = results[branch][0]
            content = True
        except ValueError:
            continue 
    return dest

#=========BEGIN MAIN UI LOOP=====================
printTitle()
print("Setup complete!\n")
#lookup = raw_input("To look up artists to navigate between, press enter! ")
while 1:
    printTitle()
    orig = lookupOrig().encode("utf8")
    origName = orig.split(" _ _ ")[0]
    printTitle()
    print("Routing from {}...".format(origName))
    traverse(orig)
    content = "r"
    while content != "o":
        dest = lookupDest().encode("utf8")
        destName = dest.split(" _ _ ")[0]
        parse(dest,mode="maker")
        content = raw_input("Route again (r) or select new origin (o)? ")
        printTitle()
        print("Routing from {}...".format(origName))
