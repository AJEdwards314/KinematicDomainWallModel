import argparse
import os
import numpy as np
import scipy.io as sio
import pandas as pd
from scipy.optimize import curve_fit


def fit(home_folder, marker_folder = '', lookup_table_folder = ''):

    if not os.path.isdir(home_folder):
        raise FileNotFoundError(f"Error: The folder {home_folder} does not exist. Please specify a new folder.")
    
    if not marker_folder:
        marker_folder = os.path.join(home_folder, 'marker_tables')
    if not os.path.isdir(marker_folder):
        raise FileNotFoundError(f"Error: The folder {marker_folder} does not exist. Please specify a new folder.")
    
    if not lookup_table_folder:
        lookup_table_folder = os.path.join(home_folder, 'lookup_tables')
    if not os.path.isdir(lookup_table_folder):
        os.mkdir(lookup_table_folder)

    # Get a list of all .mat files in the folder
    mat_files = [f for f in os.listdir(marker_folder) if f.endswith('.mat')]

    # Initialize tables for constants of model fitting
    interp_maxVel_c0 = []
    interp_maxVel_c1 = []
    interp_maxVel_c2 = []
    interp_maxVel_c3 = []
    interp_d0 = []
    interp_d1 = []
    interp_k0 = []
    interp_k1 = []
    interp_k2 = []
    interp_k3 = []
    interp_k4 = []
    
    # List of param corners to track the order
    param_list = []
    
    # Process each .mat file
    for file_name in mat_files:
        full_file_path = os.path.join(marker_folder, file_name)
    
        # Load the .mat file
        print(full_file_path)

        mat_data = sio.loadmat(full_file_path)

        print(mat_data)

        data_table = mat_data['dataTable']
    
        J = data_table[:, 0]
        max_vel = data_table[:, 1]
        time_constant = data_table[:, 2]
        drift_dist = data_table[:, 3]
    
        # Extract parameter values from file name
        base_name, _ = os.path.splitext(file_name)
    
        Aex_s = float(base_name.split('_Aex=')[1].split('_')[0])
        Ku_s = float(base_name.split('_Ku=')[1].split('_')[0])
        A_s = float(base_name.split('_A=')[1].split('_')[0])
        Msat_s = float(base_name.split('_Msat=')[1].split('_')[0])
        W_s = float(base_name.split('_W=')[1].split('_')[0])
    
        B_anis_s = (Ku_s / (0.5 * Msat_s) - (4 * np.pi * 1e-7) * Msat_s)
    
        # Append current parameter set
        current_param = [Aex_s, Ku_s, B_anis_s, A_s, Msat_s, W_s]
        param_list.append(current_param)
    
        # Fit max velocity to cubic model
        J_fit = J / J[0]
        weights = max_vel ** 2
        print(J_fit)
        print(max_vel)
        cubic_params, _ = curve_fit(cubic_model, J_fit, max_vel, p0=[1, 1, 1, 1], sigma=weights)

        # Adjust coefficients for unscaled J
        c3 = cubic_params[0] / (J[0] ** 3)
        c2 = cubic_params[1] / (J[0] ** 2)
        c1 = cubic_params[2] / J[0]
        c0 = cubic_params[3]

        # Fit drift distance to linear model
        drift_params, _ = curve_fit(linear_model, max_vel, drift_dist, p0=[1], sigma=drift_dist ** 1)
        d0 = 1 / drift_params[0]
    
        # Calculate d2
        time_inv = 1/time_constant - d0
        d1 = np.linalg.lstsq(J[:, np.newaxis], time_inv, rcond=None)[0][0]

        k0 = d0 * c0
        k1 = d0 * c1 + d1 * c0
        k2 = d0 * c2 + d1 * c1
        k3 = d0 * c3 + d1 * c2
        k4 = d1 * c3
    
        # Append model constants to respective lists
        interp_maxVel_c0.append(c0)
        interp_maxVel_c1.append(c1)
        interp_maxVel_c2.append(c2)
        interp_maxVel_c3.append(c3)
        interp_d0.append(d0)
        interp_d1.append(d1)
        interp_k0.append(k0)
        interp_k1.append(k1)
        interp_k2.append(k2)
        interp_k3.append(k3)
        interp_k4.append(k4)
    
    # Save lookup tables
    columns = ['Aex', 'Ku', 'B_anis', 'A', 'Msat', 'W', 'c0', 'c1', 'c2', 'c3', 'd0', 'd1', 'k0', 'k1', 'k2', 'k3', 'k4']
    data = np.column_stack([param_list, interp_maxVel_c0, interp_maxVel_c1, interp_maxVel_c2, interp_maxVel_c3, interp_d0, interp_d1, interp_k0, interp_k1, interp_k2, interp_k3, interp_k4])
    df = pd.DataFrame(data, columns=columns)
    
    # Write to .csv file
    df.to_csv(os.path.join(lookup_table_folder, 'lookup_all.csv'), index=False)
    
def cubic_model(x, b3, b2, b1, b0):
    return b3 * x**3 + b2 * x**2 + b1 * x + b0

def linear_model(x, b):
    return b * x

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Finds kinematic model constants for each parameter corner.")
    parser.add_argument("home_folder", type=str, help="The master directory.")  # Positional argument
    parser.add_argument("--marker_folder", type=str, default='', help="The directory storing the extracted max_vel and drift constants")  # Positional argument
    parser.add_argument("--lookup_table_folder", type=str, default='', help="The directory to put the model lookup table")  # Positional argument
    parser.add_argument("--params", type=str, default='', nargs='+', help="Pass in parameters to include in lookup table")

    args = parser.parse_args()
    fit(args.home_folder, args.marker_folder, args.lookup_table_folder)