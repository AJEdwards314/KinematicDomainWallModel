import os
import numpy as np
import scipy.io as sio
import matplotlib.pyplot as plt
import argparse
import re

def extract(home_folder, sim_folder = '', raw_data_folder = '', with_ext_centerwall = True):
    
    # Check if home_folder exists
    if not os.path.isdir(home_folder):
        raise FileNotFoundError(f"Error: The folder {home_folder} does not exist.")

    if not sim_folder:
        sim_folder = os.path.join(home_folder, 'simulations')
    if not os.path.isdir(sim_folder):    
        raise FileNotFoundError(f"Error: The folder {sim_folder} does not exist.")

    if not raw_data_folder:
        raw_data_folder = os.path.join(home_folder, 'raw_data')    
    if not os.path.isdir(raw_data_folder):
        os.mkdir(raw_data_folder)

    # Get a list of all .out folders in the folder
    file_pattern = '*.out'
    out_folders = [f for f in os.listdir(sim_folder) if f.endswith('.out')]
    
    # Loop over each .out file
    for mumax_out_folder in out_folders:
        full_folder_path = os.path.join(sim_folder, mumax_out_folder)
        print(f"Now reading {full_folder_path}")
    
        # Parse the file name to extract parameters
        base_name = os.path.basename(mumax_out_folder)
        m = re.match(r'^(.+)\.out$', base_name)
        if m:
            base_name = m.group(1)
    
        # Extract J (current density) and RT (runtime) from the file name
        j_val = float(base_name.split('_J=')[1].split('_')[0])
        rt_val = float(base_name.split('_RT=')[1].split('_')[0])
    
        # Load the table data
        table_file = os.path.join(full_folder_path, 'table.txt')
        if not os.path.isfile(table_file):
            raise FileNotFoundError(f"Error: The table file {table_file} does not exist.")
    
        data_analyzed = np.loadtxt(table_file, skiprows=1)
    
        # Determine rows and columns of data
        rows, columns = data_analyzed.shape
    
        # Shift data to calculate position/velocity values
        if with_ext_centerwall:
            data_shift = np.hstack([np.ones((rows, 1)), data_analyzed[:, 4:columns-3]])
            d_diff = data_shift - data_analyzed[:, 4:columns-2]
            x = np.arange(4, columns - 2)
        else:
            data_shift = np.hstack([np.ones((rows, 1)), data_analyzed[:, 4:columns-2]])
            d_diff = data_shift - data_analyzed[:, 4:columns-1]
            x = np.arange(4, columns - 1)
    
        # Generate current profile
        current = np.zeros(rows)
        for i in range(rows):
            if data_analyzed[i, 0] <= rt_val:
                current[i] = j_val
    
        # Calculate domain wall position
        dw_position = np.zeros(rows)
        for i in range(rows):
            dw_position[i] = np.sum(d_diff[i, :] * x) / np.sum(d_diff[i, :])
    
        if with_ext_centerwall:
            dw_position_shift = dw_position + data_analyzed[:, -2] * 1e9 - dw_position[0]
        else:
            dw_position_shift = dw_position - dw_position[0]

        position_step = 1e-9 # (1nm) !! Change if position step size changes
        dw_position_scaled = dw_position_shift * position_step

        # Plot position and velocity
        plt.figure()
        plt.plot(data_analyzed[:, 0] * 1e9, dw_position_scaled * 1e9, label="DW Position", color='blue')
        plt.ylabel("Domain wall position (nm)")
        plt.xlabel("Time (ns)")
    
        plt.twinx()
        plt.plot(data_analyzed[:, 0] * 1e9, current / 1e12, label="Current Density", color='red')
        plt.ylabel("Current Density (10^12 A/m^2)")
    
        plt.title("Domain Wall Position and Current Density")
        plt.tight_layout()
        plt.savefig(f"{full_folder_path}/position.png")
        plt.close()
    
        # Calculate velocity
        n = 2
        dw_next = np.roll(dw_position_scaled, -n)
        dw_next[-n:] = 0
    
        time_next = np.roll(data_analyzed[:, 0], -n)
        time_next[-n:] = 0
    
        delta_velocity = (dw_position_scaled - dw_next) / (data_analyzed[:, 0] - time_next)
        delta_velocity[-1] = delta_velocity[-3]
        delta_velocity[-2] = delta_velocity[-3]
    
        plt.figure()
        plt.plot(data_analyzed[:, 0] * 1e9, dw_position_scaled * 1e9, label="DW Position", color='blue')
        plt.ylabel("Domain wall position (nm)")
        plt.xlabel("Time (ns)")

        plt.twinx()
        plt.plot(data_analyzed[:, 0] * 1e9, delta_velocity, label="DW Velocity", color='red')
        plt.ylabel("Domain wall velocity (m/s)")
        plt.grid()
        plt.tight_layout()
        plt.savefig(f"{full_folder_path}/velocity.png")
        plt.close()
    
        # Save time, position, and velocity to .mat file
        time = data_analyzed[:, 0]
        dw_position = dw_position_scaled
        dw_velocity = delta_velocity

        sio.savemat(f"{full_folder_path}/data.mat", {"time": time, "dwPosition": dw_position, "dwVelocity": dw_velocity})
        sio.savemat(f"{raw_data_folder}/{base_name}.mat", {"time": time, "dwPosition": dw_position, "dwVelocity": dw_velocity})
    
        print(f"Processed and saved data for {mumax_out_folder}")

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Extracts DW position from output .txt files.")
    parser.add_argument("home_folder", type=str, help="The master directory.")  # Positional argument
    parser.add_argument("--sim_folder", type=str, default='', help="The directory storing the time-resolved DW motion data")  # Positional argument
    parser.add_argument("--raw_data_folder", type=str, default='', help="The directory to put the output data_files")  # Positional argument
    parser.add_argument("--with_ext_centerwall", nargs=1, type=bool, default=True, help="True if ext_centerWall was used in mumax")  # Optional argument

    args = parser.parse_args()

    extract(args.home_folder, args.sim_folder, args.raw_data_folder, args.with_ext_centerwall)