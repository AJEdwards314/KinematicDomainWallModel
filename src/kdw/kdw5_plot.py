import argparse
import os
import numpy as np
import csv
import matplotlib.pyplot as plt
import pandas as pd
import scipy.io as sio
import re

def plot(home_folder, error_folder = '', aggregate_error_folder = ''):
    if not os.path.isdir(home_folder):
        raise FileNotFoundError(f"Error: The folder {home_folder} does not exist.")
    
    if not error_folder:
        error_folder = os.path.join(home_folder, 'error_tables')
    if not os.path.isdir(error_folder):
        raise FileNotFoundError(f"Error: The folder {error_folder} does not exist.")
    
    if not aggregate_error_folder:
        aggregate_error_folder = os.path.join(home_folder, 'aggregate_error_plots')
    if not os.path.isdir(aggregate_error_folder):
        os.mkdir(aggregate_error_folder)

    full_file_path = os.path.join(error_folder, "all_sims_error.csv")
    # Read csv file into a pandas DataFrame
    df = pd.read_csv(full_file_path)

    plot_error_by_J(df, aggregate_error_folder, 'errors_all.png')
    plot_error_by_J(df, aggregate_error_folder, 'errors_B_350e-3.png', [{'Msat':1.2e6, 'Ku':1.11e6}, {'Msat': 7.95e5, 'Ku':5.36e5}])
    plot_error_by_J(df, aggregate_error_folder, 'errors_B_020e-3.png', [{'Msat':1.2e6, 'Ku':9.17e5}, {'Msat': 7.95e5, 'Ku':4.05e5}])
    plot_error_by_J(df, aggregate_error_folder, 'errors_W_50.png', [{'W':50e-9}])
    plot_error_by_J(df, aggregate_error_folder, 'errors_W_100.png', [{'W':100e-9}])
    plot_error_by_J(df, aggregate_error_folder, 'errors_A_01.png', [{'A':0.01}])
    plot_error_by_J(df, aggregate_error_folder, 'errors_A_05.png', [{'A':0.05}])
    plot_error_by_J(df, aggregate_error_folder, 'errors_Msat_12e5.png', [{'Msat':1.2e6}])
    plot_error_by_J(df, aggregate_error_folder, 'errors_Msat_795e3.png', [{'Msat':7.95e5}])
    plot_error_by_J(df, aggregate_error_folder, 'errors_Aex_11e-12.png', [{'Aex':11e-12}])
    plot_error_by_J(df, aggregate_error_folder, 'errors_Aex_31e-12.png', [{'Aex':31e-12}])
    plot_error_by_J(df, aggregate_error_folder, 'errors_indiv.png', [{'Aex':31e-12, 'Ku': 1.11e6, 'A':0.05, 'W':100e-9}])
            
            
def plot_error_by_J(df, aggregate_error_folder, img_name, column_vals = []):
    # select all rows where the specified column: value pairs in column_vals are within 0.1%
    df_temp = df.copy()

    if column_vals:
        df_selected = None
        for column_set in column_vals:
            df_temp = df.copy()
            for column, value in column_set.items():
                df_temp = df_temp[df_temp[column].between(value * 0.999, value * 1.001)]
            if df_selected is None:
                df_selected = df_temp
            else:
                df_selected = pd.concat([df_selected, df_temp])
    else:
        df_selected = df.copy()

    # For each value of J, average each type or error and save to a new dataframe
    df_avg = df_selected.groupby('J').mean().reset_index().sort_values(by='J')
    df_std = df_selected.groupby('J').std().reset_index().sort_values(by='J')
    df_upper_quartile = df_selected.groupby('J').quantile(0.75).reset_index().sort_values(by='J')
    df_lower_quartile = df_selected.groupby('J').quantile(0.25).reset_index().sort_values(by='J')

    #print(df_avg)

    # plot rmse_J_on, rmse_J_off, err_pos, and err_maxvel columns against J
    plt.figure(figsize=(4, 3), dpi=600)
    #set color to red

    # change line thickness of plot
    plt.errorbar(df_avg['J']/1e9-0.75, df_avg['rmse_J_on' ]*100, yerr=np.vstack([df_lower_quartile['rmse_J_on' ], df_upper_quartile['rmse_J_on' ]])*100, marker='s', markersize=3, color='blue' , linewidth=1.25, capsize=2.5, elinewidth=0.5)
    plt.errorbar(df_avg['J']/1e9-0.25, df_avg['err_maxvel']*100, yerr=np.vstack([df_lower_quartile['err_maxvel'], df_upper_quartile['err_maxvel']])*100, marker='s', markersize=3, color='red'  , linewidth=1.25, capsize=2.5, elinewidth=0.5)
    plt.errorbar(df_avg['J']/1e9+0.25, df_avg['rmse_J_off']*100, yerr=np.vstack([df_lower_quartile['rmse_J_off'], df_upper_quartile['rmse_J_off']])*100, marker='s', markersize=3, color='green', linewidth=1.25, capsize=2.5, elinewidth=0.5)
    plt.errorbar(df_avg['J']/1e9+0.75, df_avg['err_pos'   ]*100, yerr=np.vstack([df_lower_quartile['err_pos'   ], df_upper_quartile['err_pos'   ]])*100, marker='s', markersize=3, color='black', linewidth=1.25, capsize=2.5, elinewidth=0.5)
    plt.ylabel('Error (%)')
    #move ylabel to the right
    plt.gca().yaxis.set_label_coords(-0.11,0.5)
    plt.xlabel('J (mA/um$^2$)')
    plt.gca().xaxis.set_label_coords(0.5,-0.07)    
    
    plt.ylim(0, 10)
    plt.xlim(0, 44)
    plt.gca().yaxis.set_major_formatter(plt.FuncFormatter(lambda x, _: '{:.0f}%'.format(x)))
    plt.gca().set_yticks(np.arange(0, 11, 2))
    plt.gca().set_yticks(np.arange(0, 11, 1), minor=True)
    plt.gca().set_xticks(np.arange(4, 44, 4))
    plt.grid()
    plt.gca().tick_params(which='both', direction='in')
    plt.gca().tick_params(which='both', top=True, right=True)

    #plt.legend()
    # save figure
    plt.savefig(os.path.join(aggregate_error_folder, img_name))    # plot rmse_J_on, rmse_J_off, err_pos, and err_maxvel columns against J
    
    



if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Aggregate error accross different parameter values and plot.")
    parser.add_argument("home_folder", type=str, help="The master directory")  # Positional argument
    parser.add_argument("--error_folder", type=str, default='', help="Folder where error tables are stored.")  # Optional argument
    parser.add_argument("--aggregate_error_folder", type=str, default='', nargs='+', help="Folder where to save aggregate error plots.") #Optional argument

    args = parser.parse_args()

    plot(args.home_folder, args.error_folder, args.aggregate_error_folder)