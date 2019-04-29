import os, sys
import xml.etree.ElementTree
from xml.dom import pulldom
import numpy as np
import csv
import createCsvs

if 'SUMO_HOME' in os.environ:
    tools = os.path.join(os.environ['SUMO_HOME'], 'tools')
    sys.path.append(tools)
else:   
    sys.exit("please declare environment variable 'SUMO_HOME'")
import traci

    
###CONSTANTS###
sumoBinary = "/home/toby/sumo-1.1.0/src/sumo"
tripFile = "croppedTrips.trips.xml"
dirname = "/home/toby/Documents/Project/cologneCroppedInputBarrier/"
pollutionInterval = 10

def parseTrips(tripFile):
    tripInfo = []
    trips = xml.etree.ElementTree.parse(tripFile).getroot()
    for trip in trips:
        tripInfo.append([(trip.attrib["id"]), float(trip.attrib["depart"])])
    return tripInfo
        
def simulation(routingAlgorithm):
    
    sumoCmd = [sumoBinary, "-c", "cologne6to8cropped.sumocfg",
               "--routing-algorithm", routingAlgorithm,
               "--tripinfo-output", routingAlgorithm+"tripOutput.xml",
               "-v",
               "--log", os.path.join(dirname, 'logs/')+routingAlgorithm+"_log.xml",
               "--vehroute-output", routingAlgorithm+"vehicleOutput.xml",
	       "--vehroute-output.cost",
	       "--vehroute-output.route-length",
               "--netstate-dump", routingAlgorithm+"rawDump.xml"
                ]
  
    traci.start(sumoCmd)
    #Steps through whilst the simulation is still running
    while traci.simulation.getMinExpectedNumber() > 0:
        if ((traci.simulation.getTime() % pollutionInterval == 0)):
            updateEdgeEfforts()
            rerouteAll()
        for vehicle in traci.simulation.getDepartedIDList():
            #If this is the vehicle departure time it reroutes by traveltime
            traci.vehicle.rerouteTraveltime(vehicle, False)
	print(traci.simulation.getTime())
        traci.simulationStep()
    traci.close()
    os.rename("emissions.xml", routingAlgorithm+"emissions.xml")
    
def updateEdgeEfforts():

    print("updateEfforts")
    time = traci.simulation.getTime()
    threshold = 400
    for edge in traci.edge.getIDList():
        weight = calculateEdgeWeight(edge)
        if (weight>threshold):
            traci.edge.adaptTraveltime(edge, 99999999999, time, time + 30)
      

def calculateEdgeWeight(edge):
    pollution = traci.edge.getCOEmission(edge) + traci.edge.getNOxEmission(edge)
    if (pollution < 1):
        pollution = 1
    
    return pollution   

def rerouteAll():
    for vehicle in traci.vehicle.getIDList():
        traci.vehicle.rerouteTraveltime(vehicle, False)
        
def main():
    global tripInfo
    global edgePollutants
    global dirname
    tripInfo = parseTrips(tripFile)
    
    algorithms = ["dijkstra"]
    for algorithm in algorithms:
        simulation(algorithm)

def processExperimentValues():
    exposures = []
    durations = []
    with open('dijkstraexposure.csv', 'rb') as csvfile:
        myFile = csv.reader(csvfile, delimiter=',', quotechar='|')
        for row in myFile:
            exposures.append(float(row[1]))
            
    with open('dijkstradurations.csv', 'rb') as csvfile:
        myFile = csv.reader(csvfile, delimiter=',', quotechar='|')
        for row in myFile:
            durations.append(float(row[1]))
    return np.mean(exposures), np.mean(durations)

def experimentMain():


    main()
    createCsvs.main()
    x, y = processExperimentValues()
    print(x)
    print(y)

experimentMain()  

