# Automated GAMESS goemetry optimization restart
import os
import sys
import re
from operator import itemgetter # to find min E in nserch

print("This script automatically creates a restart .inp for GAMESS.")
print("Please ensure that folder paths and file names do not contain any spaces!")
print("This version doesn't support .cobaltlog files.")

# User input to locate files
folderPath = input("\nEnter directory: ")

try:
    os.chdir(folderPath.strip())
except:
    sys.exit("ERROR: CHECK DIRECTORY INPUT!")

suggestFile = ""
for file in os.listdir():
    if file.endswith(".inp"):
        suggestFile = file[:-4]
        break

fileName = input("Enter file name (without extension) [{}]: ".format(suggestFile)) or suggestFile
basis = input("Single or mixed basis set(s)? S/[M]: ") or "M"

# Check if converged
converged = False
try:
    with open(fileName+".log", "r") as logFile:
        for line in logFile:
            if "EQUILIBRIUM GEOMETRY LOCATED" in line:
                converged = True
                print("EQUILIBRIUM GEOMETRY LOCATED! Extracting results...")
                break
except:
    sys.exit("ERROR: LOG FILE NOT FOUND!")

# If converged: extract final coordinates and $VEC
"""
How: extract (inclusive) all lines between RESULTS FROM SUCCESSFUL RHF
     and the first $END statement that follows in .dat file.
"""
if converged:
    try:
        with open(fileName+".dat", "r") as datFile, open("optimized.txt", "w") as outFile:
            extract = False
            for line in datFile:
                if "RESULTS FROM SUCCESSFUL RHF" in line:
                    extract = True
                    outFile.write(line)
                    continue
                elif "$END" in line:
                    extract = False
                    continue
                elif extract:
                    outFile.write(line)
            outFile.write(" $END")
        print("Optimized structure has been written to optimized.txt")
    except:
        sys.exit("ERROR: DAT FILE NOT FOUND!")
    sys.exit(0)

# Find lowest energy NSERCH step 
nserch = []
try:
    with open(fileName+".log", "r") as logFile:
        nserch = [line for line in logFile if "NSERCH" in line]
except:
    sys.exit("ERROR: LOG FILE NOT FOUND!")

nserch = nserch[2::3] # only keep lines that contain E, GRAD. MAX. and R.M.S.

for index, line in enumerate(nserch): # only keep energy values
    match = re.search("-[0-9]*[.]?[0-9]+", line)
    nserch[index] = float(match.group(0))

minIndex = min(enumerate(nserch), key=itemgetter(1))[0] # index of min E

print("\nNSERCH {} has the minimum E={} in {}.log.".format(
    minIndex,nserch[minIndex],fileName))

# Extract coordinates and $VEC of min E goemetry
"""
How: extract (inclusive) all lines between DATA FROM NSERCH= minIndex
     and the first $END statement that follows.
"""
minEnergyGeom = []
try:
    with open(fileName+".dat", "r") as datFile, open("vec.txt", "w") as outFile:
        extract = False
        targets = ["DATA FROM NSERCH=", str(minIndex)]
        for line in datFile:
            if all(target in line for target in targets):
                extract = True
                minEnergyGeom.append(line)
                outFile.write(line)
                continue
            elif "$END" in line:
                extract = False
                continue
            elif extract:
                minEnergyGeom.append(line)
                outFile.write(line)
        minEnergyGeom.append(" $END")
        outFile.write(" $END")
        print("Lowest E geometry has been written to vec.txt")
except:
    sys.exit("ERROR: DAT FILE NOT FOUND!")

# Extract $VEC from minEnergyGeom
for index, line in enumerate(minEnergyGeom):
    if "CLOSED SHELL ORBITALS" in line:
        splitIndex = index
        break

vec = minEnergyGeom[splitIndex:]
for i in range(3): # comment out the source info of $VEC
    vec[i] = "! " + vec[i]

# Calculate NORB (number of orbitals) from extracted $VEC
NORB = 0
flagZero = False
flagNine = False

for line in vec: # count 100s segments of orbitals
    if line[:2] == "99" and flagNine == False:
        flagZero = True
        flagNine = True
    elif line[:3] == " 0 " and  flagZero == True:
        NORB += 100
        flagZero = False
        flagNine = False

extraORB = int(vec[-2][:2]) # Orbitals after the last 100 segment
NORB += extraORB

# Extract coordiantes from minEnergyGeom and add custom basis sets
coordinates = []
if basis =="S" or basis == "s":
    for line in minEnergyGeom[4:splitIndex]:
        coordinates.append(line.strip() + "\n")
elif basis == "M" or basis == "m":
    """Please change basis sets as required!"""
    for line in minEnergyGeom[4:splitIndex]:
        if "O" in line:
            coordinates.append(line.strip() + "\n" + "APCseg-1\n" + "\n")
        elif "N" in line:
            coordinates.append(line.strip() + "\n" + "APCseg-1\n" + "\n")
        elif "C" in line:
            coordinates.append(line.strip() + "\n" + "APCseg-1\n" + "\n")
        elif "H" in line:
            coordinates.append(line.strip() + "\n" + "PCseg-1\n" + "\n")
else:
    sys.exit("ERROR: BASIS INPUT NOT RECOGNIZED! ENTER M or S.")

coordinates.append(" $END\n")

# Free up memory
del nserch
del minEnergyGeom

# Extract header from original .inp file
try:
    # Find $DATA line
    with open(fileName+".inp", "r") as inpFile:
        for index, line in enumerate(inpFile):
            if "$DATA" in line:
                dataIndex = index + 3
                break
    # Copy header
    with open(fileName+".inp", "r") as inpFile:
        inpHeader = [next(inpFile) for i in range(dataIndex)]
except:
    sys.exit("ERROR: INP FILE NOT FOUND!")

# Add/update $GUESS group
guess = False
guessIndex = 0
for index, line in enumerate(inpHeader):
    if "$GUESS" in line:
        guess = True
        guessIndex = index
        break

if guess:
    inpHeader[guessIndex] = " $GUESS GUESS=MOREAD NORB={} $END\n".format(NORB)
else:
    endTargets = ["$END", "$End", "$end"]
    endIndices = []
    for index, line in enumerate(inpHeader): # find line of last $END in inpHeader
        if any(target in line for target in endTargets):
            endIndices.append(index)
    inpHeader.insert(endIndices[-1]+1, " $GUESS GUESS=MOREAD NORB={} $END\n".format(NORB))

# Output user input
outDir = input("\nEnter output directory [same as input]: ") or folderPath
outFileName = input("Enter file name (without extension) [{}]: ".format(fileName)) or fileName

# Prevent overwritting other .inp files
while os.path.isfile(outDir+"/"+outFileName+".inp"):
    print("WARNING: overwritting another .inp file has been prevented!")
    print("Please change output directory, or output file name, or both or delete existing .inp file yourself.")
    outDir = input("\nEnter output directory [same as input]: ") or folderPath
    outFileName = input("Enter file name (without extension) [{}]: ".format(fileName)) or fileName

# Go to output directory
if not os.path.exists(outDir):
    os.makedirs(outDir)
os.chdir(outDir)

# Write new .inp file:
with open(outFileName+".inp", "w") as outFile:
    for line in inpHeader:
        outFile.write(line)
    for line in coordinates:
        outFile.write(line)
    for line in vec:
        outFile.write(line)
print("New input file {} has been written to output directory.".format(fileName+".inp"))
