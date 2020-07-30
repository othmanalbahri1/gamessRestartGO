# gamessRestartGO
A script to automatically construct restart [GAMESS](https://en.wikipedia.org/wiki/GAMESS_(US)) geometry optimization .inp files.

There are two versions the script:
1. If you run GAMESS on a supercomputer that uses [COBALT](https://www.anl.gov/mcs/cobalt-componentbased-lightweight-toolkit), use rstGO.py. This version adds the COBALT run queue ID to the restart .inp file to help you keep track of restart sequences.
2. If your GAMESS workflow doesn't include COBALT (e.g. if you run GAMESS locally or on a supercomputer that uses different resource management software), use restGO_nonCobalt.py. In this case, you can implement your own way of keeping track of restart sequences; e.g. separate folders or appending "rst1" ... etc to your new .inp file name.

# Dependencies
- This script was written and tested on Python 3.8.3.
- `os`, `sys`, `re`, `operator` libraries.

# Input
The script is command line based for simplicity. Please make sure that your input/output directories and file names do not contain white-spaces.

# How it works
I've added as many comments as practically possible to help you understand what each part of the script does - to make it easy to modify. But in a nutshell, the script:
- assumes that the run's `.inp`, `.log` and `.dat` files are all in the directory you specify.
- checks the `.log` file for convergence. If converged, it outputs the optimized structure and its `$VEC` group to a new file `vec.txt` in the same directory. If not converged, it finds the `NSERCH` step with the lowest energy and extracts the corresponding coordinates and `$VEC` from the `.dat` file.
- scrapes GAMESS instructions (` $` groups) from the original `.inp` file:
  - COBALT version: adds `! Restarted from XXXXX` to header, where `XXXXX` is the queue id number of the original `.inp` file.
  - All versions: counts `NORB` of extracted `$VEC` and adds/updates ` $GUESS` group in header.
- Writes a new `.inp` file that's ready for your restart run.

## Custom basis sets in `$DATA`:
  Restarting GAMESS geometry optimization runs with custom `$DATA` basis sets is cumbersome. This script gives you the option to automatically insert basis set groups in `$DATA`. However, you need to modify the section of the script labelled `# Extract coordinates from minEnergyGeom and add custom basis sets` to suit your needs. The defaults are `APCseg-1` on C, N, O and `PCseg-1` on H atoms.
  
# Disclaimer
I've tried to anticipate mistakes and put guards in place to prevent input/output errors and overwriting existing files. However, I'd recommend that you copy the directory that contains the files of the GAMESS run you'd like to restart to a new directory and run the scrip on these copied files just in case something goes wrong. Also, check that the output files make sense!

I've written this script mainly for personal use but put it here in case it's useful to others - use at your own risk! If you catch bugs, have questions, or need minor modifications please add an issue and I'll do my best to help.
