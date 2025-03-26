import os
import numpy as np
import scipy.io as sio
import pandas as pd
from scipy.ndimage import gaussian_filter
import matplotlib.pyplot as plt
import argparse
import re

def analyze(home_folder, raw_data_folder = '', marker_folder = '', smoothed_data_folder = '', smoothed_img_folder = '', match_params = {}):

    # Check if home_folder exists
    if not os.path.isdir(home_folder):
        raise FileNotFoundError(f"Error: The folder {home_folder} does not exist.")

    if not raw_data_folder:
        raw_data_folder = os.path.join(home_folder, 'raw_data')    
    if not os.path.isdir(raw_data_folder):
        raise FileNotFoundError(f"Error: The folder {raw_data_folder} does not exist.")

    if not marker_folder:
        marker_folder = os.path.join(home_folder, 'marker_tables')
    if not os.path.isdir(marker_folder):
        os.mkdir(marker_folder)


    if not smoothed_data_folder:
        smoothed_data_folder = os.path.join(home_folder, 'smoothed_data')
    if not os.path.isdir(smoothed_data_folder):
        os.mkdir(smoothed_data_folder)

    if not smoothed_img_folder:
        smoothed_img_folder = os.path.join(home_folder, 'smoothed_images')
    if not os.path.isdir(smoothed_img_folder): 
        os.mkdir(smoothed_img_folder)

    # Get all .mat files in the folder
    mat_files = [f for f in os.listdir(raw_data_folder) if f.endswith('.mat')]
    
    # Init master simulation data structure:
    simulations = []
    
    # Loop through each .mat file
    for mat_file in mat_files:
        full_file_path = os.path.join(raw_data_folder, mat_file)
        #print(f"INFO: Now reading {full_file_path}")
    
        # Load data from the .mat file
        mat_data = sio.loadmat(full_file_path)
        time = mat_data['time'][0]
        dw_position = mat_data['dwPosition'][0]
        dw_velocity = mat_data['dwVelocity'][0]

        negate = -1 if (sum(dw_velocity) < 0) else 1
    
        # Extract J (current density) and runtime (RT) from the file name
        base_name = os.path.splitext(os.path.basename(mat_file))[0]
        
        params = {}
        param_strings = base_name.split('_')
        pattern_r = r'^(.+)=(.+)$'
        for param_string in param_strings:
            match = re.match(pattern_r, param_string)
            if match:
                params[match.group(1)] = match.group(2)

        folder_is_param_match = True
        for match_param, match_value in match_params.items():
            if match_param not in params:
                folder_is_param_match = False
            else:
                if match_value != params[match_param]:
                    folder_is_param_match = False
        if not folder_is_param_match:
            #print(f"INFO: {base_name} not not match the specified match parameters: {match_params}. Skipping.")
            continue
        else:
            print(f"INFO: Now reading {base_name}.")

        if 'J' in params:
            J = float(params['J'])
            del params['J']
        else:
            print(f"ERROR: No paramter 'J' found in filename of f{base_name}. Skipping.")
            continue
        if 'RT' in params:
            RT = float(params['RT'])
            del params['RT']
        else:
            print(f"ERROR: No paramter 'RT' found in filename of f{base_name}. Skipping.")
            continue
    
        # Generate current profile
        current = np.zeros_like(time)
        current_end = -1
        for i, t in enumerate(time):
            if t <= RT:
                current[i] = J
            else:
                if current_end == -1:
                    current_end = i
                current[i] = 0
    
        # Smooth velocity data
        smooth_vel = gaussian_filter(dw_velocity, 25)
        
        sio.savemat(f"{smoothed_data_folder}/{base_name}.mat", {"time": time, "dwPosition": dw_position, "dwVelocity": smooth_vel})
    
        # Plot position and velocity
        plt.figure()
        try:
            fig, ax1 = plt.subplots()
    
            ax1.set_xlabel('Time (ns)')
            ax1.set_ylabel('Domain wall position (nm)', color='blue')
            ax1.plot(time * 1e9, dw_position * 1e9, 'b-', label='DW position')
            ax1.tick_params(axis='y', labelcolor='blue')
    
            ax2 = ax1.twinx()
            ax2.set_ylabel('Domain wall velocity (m/s)', color='red')
            ax2.plot(time * 1e9, smooth_vel, 'r-', label='DW velocity')
            ax2.tick_params(axis='y', labelcolor='red')
    
            fig.tight_layout()
            plt.title('Domain Wall Position and Velocity')
    
            # Save the plot
            plt.savefig(os.path.join(smoothed_img_folder, f"{base_name}_smooth.png"))
        except Exception as e:
            print(f"Could not save figure: {e}")
        plt.close('all')
    
        # Calculate quantities
        max_vel = negate * np.max(np.abs(smooth_vel[current_end-1]))
    
        time_constant = time[np.where(np.abs(smooth_vel - smooth_vel[current_end - 1]) < abs(max_vel) / np.exp(1))[0][0]]
    
        drift_dist = negate * np.abs(dw_position[-1] - dw_position[current_end])
    
        if np.abs(smooth_vel[-1]) > 0.01 * abs(max_vel):
            print("WARNING: DW not stopped by end of simulation.")
    
        simulation = {'params': params, 'J': J, 'max_vel': max_vel, 'time_constant': time_constant, 'drift_dist': drift_dist}
        simulations.append(simulation)

    param_corners = []
    for simulation in simulations:
        params = simulation['params']
        if params not in param_corners:
            param_corners.append(params)
    for params in param_corners:
        data_table = np.empty((0,4))
        for simulation in simulations:
            if params != simulation['params']:
                continue
            data_table = np.vstack([data_table, [simulation['J'], simulation['max_vel'], simulation['time_constant'], simulation['drift_dist']]])

        data_table = data_table[data_table[:, 0].argsort()]  # Sort by J values

        param_str = '_'.join([f"{param}={params[param]}" for param in sorted(params.keys())])

        output_file_name = f"dataTable_{param_str}.mat"
        sio.savemat(os.path.join(marker_folder, output_file_name), {"dataTable": data_table})
    
if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Smooths DW motion and extracts max velocity and time constant markers.")
    parser.add_argument("home_folder", type=str, help="The master directory")  # Positional argument
    parser.add_argument("--raw_data_folder", type=str, default='', help="The directory storing the time-resolved DW motion data")  # Positional argument
    parser.add_argument("--marker_folder", type=str, default='', help="The directory to store the resultant data tables")  # Positional argument
    parser.add_argument("--smoothed_data_folder", type=str, default='', help="The directory to store the smoothed time-resolved data")  # Positional argument
    parser.add_argument("--smoothed_img_folder", type=str, default='', help="The directory to store the images")  # Positional argument
    parser.add_argument("--match_params", type=str, default='', nargs='+', help="Pass in target parameter values like: Msat 5e7 Aex 3e4")  # Optional argument

    args = parser.parse_args()

    match_params = {}
    if 'match_params' in args:
        for i in range (0, len(args.match_params), 2):
            match_params[args.match_params[i]] = args.match_params[i+1]

    analyze(args.home_folder, args.raw_data_folder, args.marker_folder, args.smoothed_data_folder, args.smoothed_img_folder, match_params)