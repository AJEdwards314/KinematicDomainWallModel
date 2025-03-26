import kdw.kdw1_extract as kdw1_extract
import kdw.kdw2_analyze as kdw2_analyze
import kdw.kdw3_fit as kdw3_fit
import kdw.kdw4_evaluate as kdw4_evaluate
import kdw.kdw5_plot as kdw5_plot
import kdw.kdw6_lookup as kdw6_lookup

# Flow for extending the Kinematic Domain Wall Model to a new set of material parameters

if __name__ == '__main__':
    # Uncomment as needed
    
    # Extract DW position from mumax data table
    kdw1_extract.extract('./completed_flow')
    # python kdw1_extract.py ./completed_flow

    # Analyze the extracted data
    #kdw2_analyze.analyze('./completed_flow')
    # python kdw2_analyze.py ./completed_flow

    # Fit the model to the analyzed data
    #kdw3_fit.fit('./completed_flow')
    # python kdw3_fit.py ./completed_flow

    # Evaluate the model one the simulation data and calculate error
    #kdw4_evaluate.evaluate('./completed_flow')
    # python kdw4_evaluate.py ./completed_flow

    # Plot the error
    #kdw5_plot.plot('./completed_flow')
    # python kdw5_plot.py ./completed_flow

    # Lookup the model parameters for a given set of material parameters
    #kdw6_lookup.lookup('./completed_flow', {'Aex': 1.1e-11, 'Ku': 1110000.0, 'A': 0.01, 'Msat': 1200000, 'W': 1e-07}) # Simulated parameter corner
    # python kdw6_lookup.py ./completed_flow --params Aex 1.1e-11 Ku 1110000.0 A 0.01 Msat 1200000 W 1e-07
    #kdw6_lookup.lookup('./completed_flow', {'Aex': 2.1e-11, 'Ku': 1110000.0, 'A': 0.01, 'Msat': 1200000, 'W': 1e-07}) # Not simulated parameter corner
    #kdw6_lookup.lookup('./completed_flow', {'Aex': 2.1e-11, 'Ku': 1110000.0, 'A': 0.03, 'Msat': 1200000, 'W': 1e-07}) # Not simulated parameter corner
    #kdw6_lookup.lookup('./completed_flow', {'Aex': 1.1e-11, 'Ku': 1210000.0, 'A': 0.01, 'Msat': 1200000, 'W': 1e-07}) # Not simulated parameter corner (parameter outside range of simulated data, returns nan)