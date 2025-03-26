import numpy as np
from scipy.interpolate import griddata
import pandas as pd
import argparse
import os
from scipy.spatial import distance

def lookup(home_folder, params, lookup_table_folder = '', error_tables_folder = ''):
    if not os.path.isdir(home_folder):
        raise FileNotFoundError(f"Error: The folder {home_folder} does not exist.")
    
    if not lookup_table_folder:
        lookup_table_folder = os.path.join(home_folder, 'lookup_tables')
    if not os.path.isdir(lookup_table_folder):
        raise FileNotFoundError(f"Error: The folder {lookup_table_folder} does not exist.") 
    # load the lookup table
    lookup_table = pd.read_csv(os.path.join(lookup_table_folder, 'lookup_all.csv'))

    if not error_tables_folder:
        error_tables_folder = os.path.join(home_folder, 'error_tables')
    if not os.path.isdir(error_tables_folder):
        print(f"Warning: Error tables folder, {error_tables_folder}, not found.  Precise confidence will not be reported.")
        error_table = None
    else:
        #load the error table
        error_table = pd.read_csv(os.path.join(error_tables_folder, 'all_corners_error.csv'))

    # find the row(s) in the lookup table that matches the parameters
    model_params = {}
    matching_rows = []
    for row in lookup_table.iterrows():
        row_data = row[1]
        match = True
        for param, value in params.items():
            if abs((row_data[param] - value) / value) > 0.025:
                match = False
                break
        if match:
            matching_rows.append(row_data)
    
    #If no rows matched, interpolate the model parameters
    if len(matching_rows) == 0:
        param_names = []
        lookup_values = []
        for param, value in params.items():
            param_names.append(param)
            lookup_values.append(value)
        
        lt_points = lookup_table[param_names].values # Hypercube micromagnetic parameter corners
        model_param_names = ['c0','c1','c2','c3','d0','d1'] # Names of the model parameters
        lt_values = lookup_table[['c0','c1','c2','c3','d0','d1']].values # Model parameters at the hypercube corners
        interpolated_model_params = griddata(lt_points, lt_values, [lookup_values], method='linear', rescale=True) # Interpolated model parameters

        final_model_params = {model_param_names[i]: interpolated_model_params[0][i] for i in range(len(model_param_names))} # Model parameter dictionary

        if final_model_params['c0'] == 'nan':
            raise ValueError(f"Error: Micromagnetic parameters outside convex hull of lookup table.")  

        final_model_params['k0'] = final_model_params['d0'] * final_model_params['c0']  # Calculate the quartic model parameters
        final_model_params['k1'] = final_model_params['d0'] * final_model_params['c1'] + final_model_params['d1'] * final_model_params['c0']
        final_model_params['k2'] = final_model_params['d0'] * final_model_params['c2'] + final_model_params['d1'] * final_model_params['c1']
        final_model_params['k3'] = final_model_params['d0'] * final_model_params['c3'] + final_model_params['d1'] * final_model_params['c2']
        final_model_params['k4'] = final_model_params['d1'] * final_model_params['c3']

        print_model_parameters(final_model_params) # Print the model parameters

        # Estimate the error and confidence based on nearby simulated corners
        if error_table is not None: 
            nearest_distance_scaled = 1000000
            nearest_row_scaled = None
            lt_points_max = lt_points.max(axis=0)
            lt_points_min = lt_points.min(axis=0)
            lt_points_scaled = (lt_points - lt_points_min) / (lt_points_max - lt_points_min)
            lookup_values_scaled = (lookup_values - lt_points_min) / (lt_points_max - lt_points_min)
            for point_scaled in lt_points_scaled:
                dist_scaled = distance.cityblock(point_scaled, lookup_values_scaled)
                if dist_scaled < nearest_distance_scaled:
                    nearest_distance_scaled = dist_scaled
                    nearest_row_scaled = point_scaled
            nearest_row_unscaled = nearest_row_scaled * (lt_points_max - lt_points_min) + lt_points_min
            nearest_params = {param_names[i]: nearest_row_unscaled[i] for i in range(len(param_names))}
            nearest_error_row = find_error_row(error_table, nearest_params)
            if nearest_error_row is not None:
                print(f"Error of nearest simulated corner: {round(nearest_error_row['err_mean_mean'] * 100, 2)}%")
                if nearest_distance_scaled <= 0.51:
                    print(f"Confidence: High - Scaled distance to nearest corner: {round(nearest_distance_scaled,2)}")
                elif nearest_distance_scaled <= 1.51:
                    print(f"Confidence: Medium - Scaled distance to nearest corner: {round(nearest_distance_scaled,2)}")
                else:
                    print(f"Confidence: Low - Scaled distance to nearest corner: {round(nearest_distance_scaled,2)}")

        return final_model_params
    
    # If one row matched, return the model parameters
    elif len(matching_rows) == 1:
        print(f"Found a row matching desired parameters in the lookup table.")
        model_params = matching_rows[0]
        final_model_params = {key: model_params[key] for key in ['c0','c1','c2','c3','d0','d1','k0','k1','k2','k3','k4']}
        print_model_parameters(final_model_params)
        if error_table is not None:
            error_row = find_error_row(error_table, params)
            if error_row is not None:
                print(f"Expected error: {round(error_row['err_mean_mean'] * 100, 2)}%")
                print(f"Confidence: 95% that error < {round(error_row['err_conf_95'] * 100,2)}%")
        return final_model_params
    
    # If multiple rows matched, raise an error
    else:
        raise ValueError(f"Error: Multiple lookup table rows matched the parameters: {params}.  You must specify more parameters to uniquely identify a row.")

# Print the model parameters for the user
def print_model_parameters(model_params):
    print(f"Model parameters:")
    for param, value in model_params.items():
        print(f"\t{param}: {value}")        

# Find the row with matching parameters in the error table
# Assumes at most one row will match
def find_error_row(error_table, params):
    matching_rows = []
    for row in error_table.iterrows():
        row_data = row[1]
        match = True
        for param, value in params.items():
            if abs((row_data[param] - value) / value) > 0.025:
                match = False
                break
        if match:
            return row_data
    return None

# Run the script
if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Returns model parameters for given micromagnetic parameter set.")
    parser.add_argument("home_folder", type=str, help="The master directory")  # Positional argument
    parser.add_argument("--lookup_table_folder", type=str, default='', help="Lookup table folder")  # Optional argument
    parser.add_argument("--error_tables_folder", type=str, default='', help="Folder to store output error tables.")  # Optional argument
    parser.add_argument("--params", type=str, default='', nargs='+', help="Pass in target parameter values like: Msat 5e7 Aex 3e4")  # Optional argument

    args = parser.parse_args()

    print(args.lookup_table_folder)

    params = {}
    if 'params' in args:
        for i in range (0, len(args.params), 2):
            params[args.params[i]] = float(args.params[i+1])

    lookup(args.home_folder, params, args.lookup_table_folder, args.error_tables_folder)
