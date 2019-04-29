import os, sys
import xml.etree.ElementTree
from xml.dom import pulldom
import createCsvs
import csv
import numpy as np

if 'SUMO_HOME' in os.environ:
    tools = os.path.join(os.environ['SUMO_HOME'], 'tools')
    sys.path.append(tools)
else:   
    sys.exit("please declare environment variable 'SUMO_HOME'")
import traci
    
###CONSTANTS###
sumoBinary = "/home/toby/sumo-1.1.0/src/sumo"
tripFile = "croppedTrips.trips.xml"
dirname = "/home/toby/Documents/Project/cologneWeightingExperiment/"
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
        if ((traci.simulation.getTime() % pollutionInterval == 0)): #updating the pollutant levels every interval, potentially change this based on results
            updateEdgeEfforts()
	    rerouteAll()
        for vehicle in tripInfo:
            if (vehicle[1] +1 == traci.simulation.getTime()): #For each vehicle trip compares the depart time to the current time to get which vehicles are leaving at that time
                #If this is the vehicle departure time it reroutes by effort (this way it can take into account pollutant levels)
                traci.vehicle.rerouteEffort(vehicle[0])
	print(traci.simulation.getTime())
        traci.simulationStep()
    traci.close()
    os.rename("emissions.xml", routingAlgorithm+"emissions.xml")

def updateEdgeEfforts():
    for edge in traci.edge.getIDList():
        weight = calculateEdgeWeight(edge)
        traci.edge.setEffort(edge, weight)

def calculateEdgeWeight(edge):
    pollution = traci.edge.getCOEmission(edge) + traci.edge.getNOxEmission(edge)
    if (pollution < 1):
        pollution = 1
    return ((pollution) * traci.edge.getTraveltime(edge))

def rerouteAll():
    for vehicle in traci.vehicle.getIDList():
        traci.vehicle.rerouteEffort(vehicle)
          
            
def main():
    global tripInfo
    global edgePollutants
    global dirname
    global vehicleUpdateCount
    edgePollutants = {}
    tripInfo = parseTrips(tripFile)
    
    algorithms = ["astar"]
    for algorithm in algorithms:
        simulation(algorithm)

def processExperimentValues():
    exposures = []
    durations = []
    with open('astarexposure.csv', 'rb') as csvfile:
        myFile = csv.reader(csvfile, delimiter=',', quotechar='|')
        for row in myFile:
            exposures.append(float(row[1]))
            
    with open('astardurations.csv', 'rb') as csvfile:
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
