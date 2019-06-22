from OCO2_source_detection import get_hotspot_coordinates, cluster_tag, get_coords_and_freq, find_scans, get_indices, get_grids, KML_Plots, make_KML
import os

path = '/Users/lbirman/SURF_JPL_2015/DATA2' #raw_input('Specify full path to folder containing (only) OCO2 L2StdND files')
output_file = 'output' #raw_input('Specify name of output file')
diagnostic_file = open(output_file + '.diagnostic.txt', "w")
std_range = 4 #input('how many standard deviations above the mode?')

meta = {'sid':'RetrievalHeader/sounding_id',
            'lon': 'RetrievalGeometry/retrieval_longitude',
            'lat': 'RetrievalGeometry/retrieval_latitude',
            'flag': 'RetrievalResults/outcome_flag',
            'timeo':'RetrievalHeader/retrieval_time_string'}

datal2 = {'xco2':'RetrievalResults/xco2',
            'surf':'RetrievalResults/surface_pressure_fph',
            'wind':'RetrievalResults/wind_speed',
            'albo2':'AlbedoResults/albedo_o2_fph',
            'albco2s':'AlbedoResults/albedo_weak_co2_fph',
            'albco2w':'AlbedoResults/albedo_strong_co2_fph',
            'aod':'AerosolResults/aerosol_total_aod',
            'lwi': 'RetrievalGeometry/retrieval_land_water_indicator'}


OCO2_spots, OCO2_ref, OCO2_all, OCO2_cluster = get_hotspot_coordinates(path,datal2,meta,std_range)

ddeg = 1 #input('degrees span = ?') #0.2
cluster,recurrance = cluster_tag(OCO2_cluster, ddeg)

means_freq = get_coords_and_freq(recurrance)
storing_arrays = find_scans(OCO2_spots)
indices = get_indices(OCO2_spots,path,datal2,meta)

key = 'xco2'
grids, spatial  = get_grids(indices,path,datal2,meta,key)
get_corners(spatial, grids)
tryout = {'/Users/lbirman/Desktop/shot.png':[[(0,0),(1,0),(0,1),(-1,1)],["XCO2",'originfile']]}

KML_Plots(tryout)
make_KML(means_freq,recurrance)
