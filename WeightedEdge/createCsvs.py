from xml.etree import ElementTree as ET
import csv
emissionsInterval = 10

#returns [time: [edge: [vehicle, vehicle...]], [edge: [vehicle, vehicle...]]...], [time...]
def parseRawFile(routingAlgorithm):
    rawDumpFile = routingAlgorithm+"rawDump.xml"
    parser = ET.iterparse(rawDumpFile)
    rawInfo = {}

    for event, element in parser:
        
        if (element.tag == 'timestep'):
            edgeDetails = {}
            edges = element.findall("edge")
            for edge in edges:
                vehicleIDs = []
                lanes = edge.findall("lane")
                for lane in lanes:              
                    vehicles = lane.findall("vehicle")
                    for vehicle in vehicles:
                        vehicleIDs.append(vehicle.get("id"))
                edgeDetails[edge.get("id")] = vehicleIDs
            rawInfo[element.get("time")] = edgeDetails
            print(element.get("time"))
            element.clear()
    return rawInfo

#Returns [intervalStart: [[edge: pollutantlevel], [edge: pollutantlevel]...], [intervalStart...
def parseEmissionsFile(routingAlgorithm):
    temp = []
    emissionsFile = routingAlgorithm+'emissions.xml'
    parser = ET.iterparse(emissionsFile)
    emissionsInfo = {}
    for event, element in parser:
        if (element.tag == 'interval'):
            intervalDetails = {}
            edges = element.findall("edge")
            for edge in edges:
                pollutantLevel = float(edge.get("CO_normed")) + float(edge.get("NOx_normed"))
                temp.append(pollutantLevel)
                intervalDetails[edge.get("id")] = pollutantLevel
            emissionsInfo[element.get("begin")] = intervalDetails
            element.clear()
    w = csv.writer(open("edgeEmissions.csv", "w"))
    for val in temp:
        w.writerow([val])
    return emissionsInfo

def totalExposure(routingAlgorithm):
    vehicleExposure = {}
    emissions = parseEmissionsFile(routingAlgorithm)
    simOutput = parseRawFile(routingAlgorithm)
    for timestep, edgeDetails in simOutput.iteritems():
        print(timestep)
        for edge, vehicles in edgeDetails.iteritems():
            if round_down(timestep) in emissions:
                roundedTime = round_down(timestep)
            else:
                roundedTime = max(emissions)
            if edge in emissions[roundedTime]:
                for vehicle in vehicles:
                    if vehicle in vehicleExposure:
                        vehicleExposure[vehicle] += emissions[roundedTime][edge]
                    else:
                        vehicleExposure[vehicle] = emissions[roundedTime][edge]
    return vehicleExposure
        
        
def round_down(num):
    num = float(num) - (float(num) % emissionsInterval)
    num = ("{0:.2f}".format((num)))
    return num

def totalDistances(routingAlgorithm):
    distances = {}
    tripOutputs = ET.parse(routingAlgorithm+'tripOutput.xml').getroot()
    for tripOutput in tripOutputs:
        distances[tripOutput.attrib["id"]] = (float(tripOutput.attrib["routeLength"]))
    return distances

def totalDurations(routingAlgorithm):
    durations = {}
    tripOutputs = ET.parse(routingAlgorithm+'tripOutput.xml').getroot()
    for tripOutput in tripOutputs:
        durations[tripOutput.attrib["id"]] = (float(tripOutput.attrib["duration"]))
    return durations

def dict2CSV(data, filename):
    w = csv.writer(open(filename, "w"))
    for key, val in data.items():
        w.writerow([key, val])

def main():
    algorithms = ["astar"]
    for algorithm in algorithms:
        dict2CSV(totalExposure(algorithm), algorithm+"exposure.csv")
        dict2CSV(totalDistances(algorithm), algorithm+"distances.csv")
        dict2CSV(totalDurations(algorithm), algorithm+"durations.csv")

