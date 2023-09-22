# KinematicDomainWallModel
Supplementary information for "Kinematic Model of Magnetic Domain Wall Motion for Fast, High-Accuracy Simulations"

### extract_DW_motion.m
- read in mumax3 output table files from specified folder, output excel and .mat files with position and velocity extracted

### DW_analysis.m 
- Should be run after extract_DW_motion, using the output .mat files
- Calculates various quantities (drift distance, time constant of velocity, max velocity) for each current density
- saves quantities to single .mat file per corner, for use in fit_model_constants.m

### fit_model_constants.m
- Use after running DW_analysis.m for each parameter corner, and compiling all corners' .mat file outputs into single folder as input
- Finds model constants by fitting mumax simulation results to model
- Create and save lookup tables for model constants to use in model implementations

### veriloga.va
- VerilogA code for SPICE device implementation

### DWSim_V=centerWall_Geom=1_Aex=11e-12_Xi=0.01_Ku=4.05e+5_A=0.01_Msat=7.95e+5_u0Hke=NaN_DMI=NaN_J=4.0e+09_RT=100e-9_W=100e-9.mx3
- sample mumax3 script for simple constant current pulse input

### DWSim_V=multiStep_Geom=1_Aex=11e-12_Xi=0.01_Ku=4.05e+5_A=0.01_Msat=7.95e+5_u0Hke=NaN_DMI=NaN_J=NaN_RT=NaN_W=100e-9.mx3
- sample mumax3 script for piecewise step current input
