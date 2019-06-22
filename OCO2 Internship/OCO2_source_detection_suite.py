import os
import numpy as np
import matplotlib.pyplot as plt
import h5py as h5
from scipy import stats
from lxml import etree
from pykml.factory import KML_ElementMaker as KML
import simplekml

def to_array(dict_of_var, granule):
    new_dict = {}
    for i in dict_of_var:
        new_dict[i] = np.array(granule.get(dict_of_var[i]))
    return new_dict

def thisof(data,func):
    new = {}
    for i in data:
        new[i] = func(data[i])
    return new

def get_hotspot_coordinates(path, data_L2, metadata_L2, std_range):

    """
    path = path to folder with OCO2 files
    data = dictionary of variable fields
    metadata = dictionary of geometrical and other fields
    """
    hotspot_full = {}
    reference = {}
    cluster = {}
    num = 0

    for filename in os.listdir(path):

        print path + '/' + filename
        granule = h5.File(path + '/' + filename, 'r')

        data = to_array(data_L2, granule)
        meta = to_array(metadata_L2, granule)

        data['xco2'] = data['xco2']*10**6
        meta['snum'] = meta['sid']%10

        #marking all indices with undesirable data
        index = []

        print len(data['lwi']), "DATA POINTS"

        for i in range(len(data['xco2'])):

            if meta['flag'][i] > 2 or data['lwi'][i] > 0:
                index.append(i)

        #removing all bad data
        for j in data:
            data[j] = np.delete(data[j], index)

        for u in meta:
            meta[u] = np.delete(meta[u], index)

        if len(data['xco2']) > 0:

            #grabs stats of everything for later comparison
            mean = thisof(data,np.mean)
            std = thisof(data,np.std)
            mode = thisof(data,stats.mode)
            hi = thisof(data,np.max)
            lo = thisof(data,np.min)

            #finds all values higher than your set threshold
            # aoi = areas of interest

            aoi = []

            threshold = np.float(mode['xco2'][0]) + np.float(std_range*std['xco2'])
            for k in enumerate(data['xco2']):
                if k[1] > threshold:
                    clip = [k[0],k[1],meta['lon'][k[0]],meta['lat'][k[0]],meta['snum'][k[0]],meta['sid'][k[0]]]
                    aoi.append(clip)

            if len(aoi) == 0:
                spots = []
                pass

            else:

                spots = []
                holder = []

                for l in range(len(aoi)-1):
                    dindy = aoi[l+1][0] - aoi[l][0]
                    if dindy < 12:
                        holder.append(aoi[l])
                    else:
                        holder.append(aoi[l])
                        spots.append(holder)
                        holder = []
                if len(aoi) > 1 and len(spots) > 0:

                    if spots[len(spots)-1][-1][0] == aoi[len(aoi)-1][0]:
                        pass
                    else:
                        holder.append(aoi[len(aoi)-1])
                        spots.append(holder)

                #print "###### HOTSPOTS ######"
                #print " There are %s possible features in %s this file " %(len(spots),filename)
                #print " Points in each feature:"
                #print " This many areas of interest: ", len(aoi)
                #for i in range(len(spots)):
                    #l = len(spots[i])
                    #print " feature %s has %s points" %(i,l)


            place = []
            just_pos = []
            for t in range(len(spots)):
                    place.append([spots[t],
                                [np.std(spots[t],axis = 0),np.mean(spots[t],axis = 0)],filename]
                                )
                    just_pos.append([np.mean(spots[t],axis = 0)[2],np.mean(spots[t],axis = 0)[3],0])

            ### IT"S HERE!!! ###
            #if num == 0:
            #    allinone = place

            #else:
            #   allinone += place
            allinone = 0

            hotspot_full[num] = place
            reference[num] = filename
            cluster[num] = [just_pos, filename]
            num += 1
        print "Done"
    return hotspot_full, reference, allinone, cluster

def spot_frequency(OCO2_all):
    x = []
    y = []
    X = []
    for i in range(len(OCO2_all)):
        x.append(OCO2_all[i][1][1][2])
        y.append(OCO2_all[i][1][1][3])
        X.append([OCO2_all[i][1][1][2],OCO2_all[i][1][1][3]])
    return x, y, X

def cluster_tag(OCO2_cluster, ddeg):
    freq = []
    tag = 1
    for i in range(len(OCO2_cluster)-1):
        arrays_ahead = np.arange(len(OCO2_cluster)-(i+1))+i+1
        for j in range(len(OCO2_cluster[i][0])):
            if OCO2_cluster[i][0][j][2] == 0:
                x0 = OCO2_cluster[i][0][j][0]
                y0 = OCO2_cluster[i][0][j][1]

            for k in arrays_ahead:
                current_col = range(len(OCO2_cluster[k][0]))
                for l in current_col:
                    x = OCO2_cluster[k][0][l][0]
                    y = OCO2_cluster[k][0][l][1]

                    if OCO2_cluster[k][0][l][2] == 0:
                        if x0 - ddeg < x < x0 + ddeg and y0 - ddeg < y < y0 + ddeg:
                            print "HIT! TARGET", i,j,x0,y0
                            print "HIT! QUERY", k,l,x,y
                            OCO2_cluster[i][0][j][2] = tag
                            OCO2_cluster[k][0][l][2] = tag
                            if [tag,[i,j,x0,y0]] in freq:
                                freq.append([tag,[k,l,x,y],OCO2_cluster[k][1]])
                            else:
                                freq.append([tag,[i,j,x0,y0],OCO2_cluster[i][1]])
                                freq.append([tag,[k,l,x,y],OCO2_cluster[k][1]])
                            print "TAG!", tag

            tag += 1

    return OCO2_cluster, freq

def get_coords_and_freq(freq):

    means_freq = {}
    count = 0
    lons = []
    lats = []
    for i in range(len(freq)-1):

        if freq[i][0] == freq[i+1][0]:
            lons.append(freq[i][1][2])
            lats.append(freq[i][1][3])
        else:
            lons.append(freq[i][1][2])
            lats.append(freq[i][1][3])
            fq = len(lons)
            lons = np.mean(lons)
            lats = np.mean(lats)
            means_freq[count] = [fq,lons,lats]
            count += 1
            lons = []
            lats = []
        lons.append(freq[i][1][2])
        lats.append(freq[i][1][3])
        fq = len(lons)
        lons = np.mean(lons)
        lats = np.mean(lats)
        means_freq[count] = [fq,lons,lats]

    return means_freq

def find_scans(OCO2_spots):
    array_to_store_arrays = {}
    for i in range(len(OCO2_spots)):
        sounding_id_array = []
        for j in range(len(OCO2_spots[i])):
            sounding_id_array.append([OCO2_spots[i][j][0][0][5],OCO2_spots[i][j][2]
])
        array_to_store_arrays[i] = (sounding_id_array)
    return array_to_store_arrays

def get_indices(OCO2_spots,path,datal2,meta):
    indices = {}
    for i in OCO2_spots:
        hold = []
        granule = h5.File(path + '/' + OCO2_spots[i][0][2], 'r')
        data1 = to_array(datal2, granule)
        meta1 = to_array(meta, granule)
        index = []


        for k in range(len(data1['xco2'])):
            if meta1['flag'][k] > 2 or data1['lwi'][k] > 0:
                index.append(k)
        for k in data1:
            data1[k] = np.delete(data1[k], index)
        for k in meta:
            meta1[k] = np.delete(meta1[k], index)


        for j in range(len(OCO2_spots[i])):
            indexs = np.where(OCO2_spots[i][j][0][0][5] == meta1['sid'])[0][0]
            hold.append([OCO2_spots[i][j][0][0][5],indexs])
        indices[OCO2_spots[i][0][2] ] = hold
        print 100*(np.float(i)/len(OCO2_spots)), '%'
    return indices

def get_grids(indices,path,datal2,metal,key):
    """
    key = string l2 data field
    """

    grids = {}
    spatial = {}

    for filename in indices:
        granule = h5.File(path + '/' + filename, 'r')
        data = to_array(datal2, granule)
        meta = to_array(metal, granule)
        sid = meta['sid']
        data['xco2'] = data['xco2']*10**6


        footprint = sid%10

        for k in range(len(sid)):

            sid[k] = int(str(sid[k])[:-1]) #sid is still sid

        all_ids = np.array(sorted(set(sid)))

        IDs = {}
        sIDs = {}

        for i in range(len(indices[filename])):
            ID = indices[filename][i][0] #sounding ID
            ID = int(str(ID)[:-1])

            x = np.where(all_ids == ID)[0]

            swaths = []

            if len(all_ids) - x < 5: #skipping the bordering case for now
                pass
            else:
                footprint_range = 5
                while footprint_range > -5:
                    swaths.append(all_ids[x-footprint_range])
                    footprint_range -= 1

                swathstore = {}
                spacestore = {}
                for a in swaths:
                    store = np.zeros(8)
                    space = np.zeros((8,2))
                    for j in range(len(sid)):
                        if a == sid[j]:
                            store[footprint[j]-1] = data[key][j]
                            space[footprint[j]-1] = [meta['lon'][j],meta['lat'][j]]
                    swathstore[a[0]] = np.array(store)
                    spacestore[a[0]] = np.array(space)

            #need information from grid[0][0], grid[0][7], grid[len(grid)-1][0], grid[len(grid)-1][7]
                grid = []#[swathstore[swaths[0]]]
                sgrid = []
                for t in range(len(swaths)-1):

                    grid.append(swathstore[ swaths[t][0] ])
                    sgrid.append(spacestore[ swaths[t][0] ])

                    dt = swaths[t+1] - swaths[t]

                    if dt <= 4:
                        pass
                    else:
                        empty = int(dt/3.3)
                        for t in range(empty):
                            grid.append(np.zeros(8))
                            sgrid.append(np.zeros(8))

                grid.append(swathstore[swaths[-1][0]])
                sgrid.append(spacestore[ swaths[-1][0] ])
            IDs[ID] = grid
            sIDs[ID] = sgrid
        grids[filename] = IDs
        spatial[filename] = sIDs


    return grids, spatial

def get_corners(spatial, grids):
    t = 0
    for filename in grids:
        for sounding_id in grids[filename]:
            t += 1
            TL = grids[filename][sounding_id][0][0]
            TR = grids[filename][sounding_id][0][7]
            BL = grids[filename][sounding_id][len(grids)-1][0]
            BR = grids[filename][sounding_id][len(grids)-1][7]
            if TL != 0 and TR != 0 and BL != 0 and BR != 0:
                TL = spatial[filename][sounding_id][0][0]
                TR = spatial[filename][sounding_id][0][7]
                BL = spatial[filename][sounding_id][len(grids)-1][0]
                BR = spatial[filename][sounding_id][len(grids)-1][7]
                print TL,TR,BL,BR
                print "Don't be a square...or do, either way"
    print t

def KML_Plots(filelist):
    """
    Goals:
    input dictionary with link to filename as i
    store lat lon of corners as tuples (lon,lat)
    filelist[i][0] = [bottom left, bottom right, top right, top left] tuples (lon,lat)
    filelist[i][1][0] = datatype
    filelist[i][1][1] = OCO2 file

    Should be evaluated over each image field
    datatype = string
    """

    kml = simplekml.Kml()

    for i in filelist:
        #print i
        name = filelist[i][1][0]
        ground = kml.newgroundoverlay(name='%s'%(name))
        ground.icon.href = i
        ground.gxlatlonquad.coords = filelist[i][0]

        print "Created file: %s_Overlays_L2StdND.kml"%(name)

        kml.save("%s_Overlays_L2StdND.kml"%(name))

def make_KML(C,B):

    fld = KML.Folder()

    new_dict = {}

    for i in C:
        new_dict[i] = "%s, %s"%(C[i][1],C[i][2])

    place_in_parse = 0

    for i in new_dict:

        fld1 = KML.Folder(
                    KML.name("%s, recurrence %s"%(i,C[i][0])))

        fld1.append(

            KML.Placemark(
                KML.Point(
                    KML.coordinates(new_dict[i])),
                    KML.name("Mean Spot %s"%(i)),
                    KML.description("Longitude = %s\n Latitude = %s\n Recurrence: %s\n"%(C[i][1],C[i][2],C[i][0]))))

        for j in np.arange(C[i][0]) + place_in_parse:
            coords = "%s, %s"%(B[j][1][2],B[j][1][3])
            spot = j - place_in_parse
            fld1.append(

                KML.Placemark(
                    KML.Point(
                        KML.coordinates(coords)),
                        KML.name( "Spot %s"%(spot) ),
                        KML.description("Longitude = %s\n Latitude = %s\n Filename: %s\n"%(B[j][1][2],B[j][1][3],B[j][2]))))

        place_in_parse += C[i][0]

        new_dict[i] = fld1

    for i in new_dict:
        fld.append(new_dict[i])

    outfile = file(__file__.rstrip('.py')+'.freq'+'.kml','w')
    outfile.write(etree.tostring(fld, pretty_print=True))
    print "Created frequency file"
