import kdw.kdw6_lookup as kdw6_lookup

# Flow for looking up model parameters from material parameters:

if __name__ == '__main__':
    # Lookup the model parameters for a given set of material parameters
    kdw6_lookup.lookup('./KinematicDomainWallModel', {'Aex': 1.1e-11, 'Ku': 1110000.0, 'A': 0.01, 'Msat': 1200000, 'W': 1e-07}) # Simulated parameter corner
    # python kdw6_lookup.py ./KinematicDomainWallModel --params Aex 1.1e-11 Ku 1110000.0 A 0.01 Msat 1200000 W 1e-07
    
    #kdw6_lookup.lookup('./KinematicDomainWallModel', {'Aex': 2.1e-11, 'Ku': 1110000.0, 'A': 0.01, 'Msat': 1200000, 'W': 1e-07}) # Not simulated parameter corner
    #kdw6_lookup.lookup('./KinematicDomainWallModel', {'Aex': 2.1e-11, 'Ku': 1110000.0, 'A': 0.03, 'Msat': 1200000, 'W': 1e-07}) # Not simulated parameter corner
    #kdw6_lookup.lookup('./KinematicDomainWallModel', {'Aex': 1.1e-11, 'Ku': 1210000.0, 'A': 0.01, 'Msat': 1200000, 'W': 1e-07}) # Not simulated parameter corner (parameter outside range of simulated data, returns nan)
