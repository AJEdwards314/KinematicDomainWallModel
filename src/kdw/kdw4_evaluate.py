import argparse
import os
import numpy as np
import csv
import matplotlib.pyplot as plt
import pandas as pd
import scipy.io as sio
import re

def evaluate(home_folder, smoothed_data_folder = '', lookup_table_folder = '', error_img_folder = '', error_folder = '', match_params = {}):
    if not os.path.isdir(home_folder):
        raise FileNotFoundError(f"Error: The folder {home_folder} does not exist.")
    
    if not smoothed_data_folder:
        smoothed_data_folder = os.path.join(home_folder, 'smoothed_data')
    if not os.path.isdir(smoothed_data_folder):
        raise FileNotFoundError(f"Error: The folder {smoothed_data_folder} does not exist.")
    
    if not lookup_table_folder:
        lookup_table_folder = os.path.join(home_folder, 'lookup_tables')
    if not os.path.isdir(lookup_table_folder):
        raise FileNotFoundError(f"Error: The folder {lookup_table_folder} does not exist.") 
    
    if not error_img_folder:
        error_img_folder = os.path.join(home_folder, 'error_images')
    if not os.path.isdir(error_img_folder):
        os.mkdir(error_img_folder)

    if not error_folder:
        error_folder = os.path.join(home_folder, 'error_tables')
    if not os.path.isdir(error_folder):
        os.mkdir(error_folder)

    lookup_table = {}
    lookup_table_path = os.path.join(lookup_table_folder, 'lookup_all.csv')
    
    if not os.path.isfile(lookup_table_path):
        raise FileNotFoundError(f"Error: The file {lookup_table_path} does not exist.")
    
    with open(lookup_table_path, mode='r') as infile:
        reader = csv.DictReader(infile)
        lookup_table = {param: [] for param in reader.fieldnames}  # Initialize empty lists per column
        
        for row in reader:
            for field in reader.fieldnames:
                lookup_table[field].append(row[field]) 

        simulations = []
        
        mat_files = [f for f in os.listdir(smoothed_data_folder) if f.endswith('.mat')]

        # Loop through each .mat file
        for mat_file in mat_files:
            full_file_path = os.path.join(smoothed_data_folder, mat_file)
            #print(f"INFO: Now reading {full_file_path}")
    
            # Load data from the .mat file
            mat_data = sio.loadmat(full_file_path)
            time = mat_data['time'][0]
            dw_position = mat_data['dwPosition'][0]
            dw_velocity = mat_data['dwVelocity'][0]
    
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

            model_index = -1

            for i in range(len(lookup_table['Msat'])):
                not_found = False
                for param, value in params.items():
                    if not param in lookup_table.keys():
                        continue
                    if abs((float(lookup_table[param][i]) - float(value)) / float(value)) > 0.01:
                        #print(lookup_table[param][i], value)
                        not_found = True
                        break
                if not not_found:
                    model_index = i
                    break

            if model_index == -1:
                print(f"ERROR: Could not find a unique parameter match for {base_name}. Skipping.")
                continue

            #print(model_index)

            # Extract the model parameters
            k0 = float(lookup_table['k0'][model_index])
            k1 = float(lookup_table['k1'][model_index])
            k2 = float(lookup_table['k2'][model_index])
            k3 = float(lookup_table['k3'][model_index])
            k4 = float(lookup_table['k4'][model_index])
            d0 = float(lookup_table['d0'][model_index])
            d1 = float(lookup_table['d1'][model_index])

            x_model, v_model, a_model = kinematic_model(k0, k1, k2, k3, k4, d0, d1, time, current)
            
            plt.figure()
            try:
                fig, ax1 = plt.subplots()
     
                ax1.set_xlabel('Time (ns)')
                ax1.set_ylabel('Domain wall position (nm)', color='blue')
                ax1.plot(time * 1e9, dw_position * 1e9, 'b-', label='DW position')
                ax1.plot(time * 1e9, x_model * 1e9, 'b--', label='DW position')
                ax1.tick_params(axis='y', labelcolor='blue')
    
                ax2 = ax1.twinx()
                ax2.set_ylabel('Domain wall velocity (m/s)', color='red')
                ax2.plot(time * 1e9, dw_velocity, 'r-', label='DW velocity')
                ax2.plot(time * 1e9, v_model, 'r--', label='DW velocity')
                ax2.tick_params(axis='y', labelcolor='red')
                
                fig.tight_layout()
                plt.title('Domain Wall Position and Velocity')
    
                # Save the plot
                plt.savefig(os.path.join(error_img_folder, f"{base_name}_smooth.png"))
            except Exception as e:
                print(f"Could not save figure: {e}")
            plt.close('all')

            rmse_J_on = np.sqrt(np.mean((x_model[0:current_end] - dw_position[0:current_end]-0.1e-9)**2)) / abs(dw_position[-1])
            rmse_J_off = np.sqrt(np.mean((x_model[current_end:] - dw_position[current_end:])**2)) / abs(dw_position[-1])
            err_pos = abs((x_model[-1] / dw_position[-1]) - 1)
            err_maxvel = abs((v_model[current_end-1] / dw_velocity[current_end-1]) - 1)
            err_mean = np.mean([rmse_J_on, rmse_J_off, err_pos, err_maxvel])
            print(rmse_J_on, rmse_J_off, err_pos, err_maxvel, err_mean)

            simulation = {'params': params, 'J': J, 'rmse_J_on': rmse_J_on, 'rmse_J_off': rmse_J_off, 'err_pos': err_pos, 'err_maxvel': err_maxvel, 'err_mean': err_mean}
            simulations.append(simulation)

        
        param_corners = []
        corners_data_table = np.empty((0,11))
        corners_param_table = np.empty((0,6))
        all_sims_table = np.empty((0,12))
        for simulation in simulations:
            params = simulation['params']
            if params not in param_corners:
                param_corners.append(params)
        for params in param_corners:
            data_table = np.empty((0,6))
            B_anis = (float(params['Ku']) / (0.5 * float(params['Msat'])) - (4 * np.pi * 1e-7) * float(params['Msat']))
            for simulation in simulations:
                if params != simulation['params']:
                    continue

                current_data = [simulation['J'], simulation['rmse_J_on'], simulation['rmse_J_off'], simulation['err_pos'], simulation['err_maxvel'], simulation['err_mean']]
                data_table = np.vstack([data_table, current_data])
                all_sims_table = np.vstack([all_sims_table, np.hstack([[params['Aex'], params['Ku'], B_anis, params['A'], params['Msat'], params['W']], current_data])])

            data_table = data_table[data_table[:, 0].argsort()]  # Sort by J values
            
            columns = ['J', 'rmse_J_on', 'rmse_J_off', 'err_pos', 'err_maxvel', 'err_mean']
            df = pd.DataFrame(data_table, columns=columns)
            param_str = '_'.join([f"{param}={params[param]}" for param in sorted(params.keys())])
            output_file_name = f"error_{param_str}.csv"
            df.to_csv(os.path.join(error_folder, output_file_name), index=False)
            
            rmse_J_on_mean =  np.mean(data_table[:, 1])
            rmse_J_on_std =    np.std(data_table[:, 1])
            rmse_J_off_mean = np.mean(data_table[:, 2])
            rmse_J_off_std =   np.std(data_table[:, 2])
            err_pos_mean =    np.mean(data_table[:, 3])
            err_pos_std =      np.std(data_table[:, 3])
            err_maxvel_mean = np.mean(data_table[:, 4])
            err_maxvel_std =   np.std(data_table[:, 4])
            err_mean_mean =   np.mean(data_table[:, 5])
            err_mean_std =     np.std(data_table[:, 5])
            err_conf_95 =     err_mean_mean + err_mean_std * 1.96 / np.sqrt(len(data_table[:, 5]))
            
            corner_data = [rmse_J_on_mean, rmse_J_on_std, rmse_J_off_mean, rmse_J_off_std, err_pos_mean, err_pos_std, err_maxvel_mean, err_maxvel_std, err_mean_mean, err_mean_std, err_conf_95]
            corners_data_table = np.vstack([corners_data_table, corner_data])
            
            corner_params = [params['Aex'], params['Ku'], B_anis, params['A'], params['Msat'], params['W']]
            corners_param_table = np.vstack([corners_param_table, corner_params])

        corners_table_columns = ['Aex', 'Ku', 'B_anis', 'A', 'Msat', 'W', 'rmse_J_on_mean', 'rmse_J_on_std', 'rmse_J_off_mean', 'rmse_J_off_std', 'err_pos_mean', 'err_pos_std', 'err_maxvel_mean', 'err_maxvel_std', 'err_mean_mean', 'err_mean_std', 'err_conf_95']
        corners_df = pd.DataFrame(np.hstack([corners_param_table, corners_data_table]), columns=corners_table_columns)        
        corners_df.to_csv(os.path.join(error_folder, 'all_corners_error.csv'), index=False)

        all_sims_columns = ['Aex', 'Ku', 'B_anis', 'A', 'Msat', 'W', 'J', 'rmse_J_on', 'rmse_J_off', 'err_pos', 'err_maxvel', 'err_mean']
        all_sims_df = pd.DataFrame(all_sims_table, columns=all_sims_columns)
        all_sims_df.to_csv(os.path.join(error_folder, 'all_sims_error.csv'), index=False)

def kinematic_model(k0, k1, k2, k3, k4, d0, d1, time, current, init_x = 0, init_v = 0, init_a = 0):
    x = np.zeros_like(time)
    x[0] = init_x
    v = np.zeros_like(time)
    v[0] = init_v
    a = np.zeros_like(time)
    a[0] = init_a
    for i in range(1, len(time)):
        dt = time[i] - time[i-1]
        if current[i] > 0:
            a_j = k4 * current[i]**4 + k3 * current[i]**3 + k2 * current[i]**2 + k1 * current[i] + k0
        elif current[i] < 0:
            a_j = -k4 * current[i]**4 + k3 * current[i]**3 - k2 * current[i]**2 + k1 * current[i] - k0
        else:
            a_j = 0
        a_damp = -v[i-1] * (d1 * abs(current[i]) + d0)
        a[i] = a_j + a_damp
        v[i] = v[i-1] + a[i] * dt
        x[i] = x[i-1] + v[i] * dt
    return x, v, a

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Extracts DW motion from .txt files.")
    parser.add_argument("home_folder", type=str, help="The master directory")  # Positional argument
    parser.add_argument("--smoothed_data_folder", type=str, default='', help="The directory to store the smoothed time-resolved data")  # Positional argument
    parser.add_argument("--lookup_table_folder", type=str, default='', help="Lookup table folder")  # Optional argument
    parser.add_argument("--error_img_folder", type=str, default='', help="Folder to store output error images.")  # Optional argument
    parser.add_argument("--error_folder", type=str, default='', help="Folder to store output error tables.")  # Optional argument
    parser.add_argument("--match_params", type=str, default='', nargs='+', help="Pass in target parameter values like: Msat 5e7 Aex 3e4")  # Optional argument

    args = parser.parse_args()

    print(args.lookup_table_folder)

    match_params = {}
    if 'match_params' in args:
        for i in range (0, len(args.match_params), 2):
            match_params[args.match_params[i]] = args.match_params[i+1]

    evaluate(args.home_folder, args.smoothed_data_folder, args.lookup_table_folder, args.error_img_folder, args.error_folder, match_params)