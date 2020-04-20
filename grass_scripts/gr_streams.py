#! python3

"""
Run GRASS watershed tool on DEMs and export SRC and P files for use with TauDEm
Experimental, don't use it!
"""


def grass_environment_00(grass_bin=r'C:\Program Files\GRASS GIS 7.8\grass78.bat'):
    """Get and/or set GRASS paths and environmental variables
    
    Parameters
    ----------
    grass_bin : str
        Path to GRASS binary. If installed via OSGeo it will be something
        like the default.

    Returns
    -------
    gisbase : str
    """
    import os
    import sys
    import subprocess
    
    #TODO: Add search for grass binary so it finds other versions
    
    ############## Copied section
    # query GRASS GIS itself for its GISBASE
    startcmd = [grass_bin, '--config', 'path']
    try:
        p = subprocess.Popen(startcmd, shell=False,
                             stdout=subprocess.PIPE, stderr=subprocess.PIPE)
        out, err = p.communicate()
    except OSError as error:
        sys.exit("ERROR: Cannot find GRASS GIS start script"
                 " {cmd}: {error}".format(cmd=startcmd[0], error=error))
    if p.returncode != 0:
        sys.exit("ERROR: Issues running GRASS GIS start script"
                 " {cmd}: {error}"
                 .format(cmd=' '.join(startcmd), error=err))
    gisbase = out.decode().strip(os.linesep)
    
    # set GISBASE environment variable
    os.environ['GISBASE'] = gisbase
    
    # define GRASS-Python environment and add to PATH
    grass_pydir = os.path.join(gisbase, "etc", "python")
    sys.path.append(grass_pydir)
  
    return gisbase


def open_location_00(dem_path, gisdb):
    """Open or create a location and mapset
    
    GRASS directory structure is gisdb/location/mapset.

    Parameters
    ----------
    dem_path : str
        Path to DEM tif file to import. Extent and resolution of the
        location will be based on it.
    gisdb : str
        Path to root GRASS project folder.

    Returns
    -------

    """
    import subprocess
    from pathlib import Path
    
    gisbase = grass_environment_00()
    grass = "grass78"  #TODO: Replace with search to find GRASS version.
    
    dem = Path(str(dem_path))
    db = Path(str(gisdb))
    
    # Create location name from dem name
    location_name = dem.name.split('_')[0]
    location_path = db.joinpath(location_name)
    
    # Create mapset name from dem name
    mapset_name = dem.name.split('_')[1]
    mapset_path = location_path.joinpath(mapset_name)
    
    if not mapset_path.exists():
        # Start GRASS, create the new mapset (and location if needed)
        grass_cmd = [grass, "-c", dem_path, "{l}/{m}".format(l=location_path,
                                                            m=mapset_name)]
        subprocess.call(grass_cmd)
        
    # Import GRASS Python bindings
    #import grass.script as gscript
    from grass.script import setup as gsetup

    # Launch session
    rcfile = gsetup.init(gisbase, gisdb, location_path, mapset_name)


def grass_setup_00(gisdb, location, mapset='PERMANENT'):
    """Start GRASS and opens the specified mapset.
    
    Requires existing database, location, and mapset. If it doesn't exist
    yet, run new_location_00()

    Parameters
    ----------
    gisdb : str
        Path to the GRASS database. This is the parent folder of the location.
    location : str
        Name of the GRASS location.
    mapset : str
        Name of the mapset. One called PERMANENT is automatically created.
    """
    
    import os
    import sys
    import subprocess

    # Location of GRASS binary, below is the default if GRASS is installed
    # w/ OSGeo
    grass7bin = r'C:\Program Files\GRASS GIS 7.8\grass78.bat'

    ############## Copied section
    # query GRASS GIS itself for its GISBASE
    startcmd = [grass7bin, '--config', 'path']
    try:
        p = subprocess.Popen(startcmd, shell=False,
                             stdout=subprocess.PIPE, stderr=subprocess.PIPE)
        out, err = p.communicate()
    except OSError as error:
        sys.exit("ERROR: Cannot find GRASS GIS start script"
                 " {cmd}: {error}".format(cmd=startcmd[0], error=error))
    if p.returncode != 0:
        sys.exit("ERROR: Issues running GRASS GIS start script"
                 " {cmd}: {error}"
                 .format(cmd=' '.join(startcmd), error=err))
    gisbase = out.decode().strip(os.linesep)

    # set GISBASE environment variable
    os.environ['GISBASE'] = gisbase

    # define GRASS-Python environment
    grass_pydir = os.path.join(gisbase, "etc", "python")
    sys.path.append(grass_pydir)

    
    # Import GRASS Python bindings
    import grass.script as gscript
    from grass.script import setup as gsetup
    
    
    # Launch session
    rcfile = gsetup.init(gisbase, gisdb, location, mapset)
    
    # # Example calls
    gscript.message('Current GRASS GIS 7 environment:')
    print(gscript.gisenv())

    # gscript.message('Available raster maps:')
    # for rast in gscript.list_strings(type='raster'):
    #     print(rast)
    #
    # gscript.message('Available vector maps:')
    # for vect in gscript.list_strings(type='vector'):
    #     print(vect)


def import_dem_00(dem_path):
    """

    Parameters
    ----------
    dem_path : str
        Path to the DEM

    Returns
    -------
    out_raster : str
        Name of the imported raster
    """

    from pathlib import Path
    
    import grass.script as gscript
    
    name_parts = Path(str(dem_path)).name.split('_')
    out_raster = '_'.join(name_parts[0:2])
    
    # Import DEM
    gscript.run_command('r.in.gdal', input=str(dem_path), output=out_raster)
    
    # Set computational region
    gscript.run_command('g.region', raster=out_raster)  # align?
    
    return out_raster


def export_raster_00(in_raster, group_parent_name, group_str, name, dem_path):
    """

    Parameters
    ----------
    in_raster : str
        Name of GRASS raster to export
    group_parent_name : str
        Name of class, example: "Surface_Flow"
    group_str : str
        Group prefix, example: "SFW"
    name : str
        Model file abbreviation, example: "P"
    dem_path : str
        Path to DEM
    """
    
    from pathlib import Path
    
    import grass.script as gscript
    
    dem = Path(dem_path)
    dsm = dem.parent
    prj = dsm.parent.parent
    
    group_parent_path = prj.joinpath(group_parent_name)
    
    grps = group_parent_path.glob(group_str + '*')
    
    if grps:
        grpnos = []
        for grp in grps:
            grpno = grp.name.split("_")[0][:-2]
            grpnos.append(int(grpno))
        new_group_no = ('0' + str(max(grpnos) + 1))[-2:]
    else:
        new_group_no = '00'
    
    new_group = group_parent_path.joinpath(group_str + new_group_no)
    Path.mkdir(new_group)
    
    # Export file path
    out_file_name = "{}{}_{}.tif".format(name, new_group_no,
                                         dem.name.split("_")[1])
    out_path = new_group.joinpath(out_file_name)
    
    # CLI command: r.out.gdal -c --overwrite input=in_raster
    # output=out_path format=GTiff type=Int16
    # createopt=COMPRESS=LZW,PREDICTOR=2,BIGTIFF=YES nodata=-32768
    
    # TODO: Export the raster with the same extent and resolution as the DEM

    gscript.run_command('r.out.gdal', input=in_raster, output=out_path,
                   format="GTiff", type="Int16",
                   createopt="COMPRESS=LZW,PREDICTOR=2,BIGTIFF=YES",
                   nodata=-32768)


def watershed_00(in_raster_name, threshold):
    """Runs r.watershed

    Parameters
    ----------
    in_raster_name : str
        Name of imported dem file
    threshold : int
        Minimum size, in map cells, of individual watersheds. 100 gives
        reasonable results for 20ft resolution

    Returns
    -------
    watershed_rasters : dict
        Output rasters {type: name}
    """
    
    import grass.script as gscript
    
    huc = in_raster_name.split('_')[0]
    num = in_raster_name[-2:]
    
    # Output Rasters
    watershed_rasters = {
        'accumulation': "{h}_acc_{n}".format(h=huc, n=num),
        'tci': "{h}_tci_{n}".format(h=huc, n=num),
        'spi': "{h}_spi_{n}".format(h=huc, n=num),
        'drainage': "{h}_drain_{n}".format(h=huc, n=num),
        'basin': "{h}_basin_{n}".format(h=huc, n=num),
        'stream': "{h}_stream_{n}".format(h=huc, n=num),
        'length_slope': "{h}_slplen_{n}".format(h=huc, n=num),
        'slope_steepness': "{h}_slpstp_{n}".format(h=huc, n=num)
        }
    
    gscript.core.run_command('r.watershed', input=in_raster_name,
                        threshold=threshold, **watershed_rasters)
    
    return watershed_rasters


##################################################################################
# mapcalc parameters:
# exp (str): expression
# quiet (bool): true to run quietly
# verbose (bool): true to run verbosely
# overwrite (bool): true to enable overwriting the output
# seed (int): integer to seed the random-number generator for the rand()
# function
# env (dict): dictionary of environment variables for child process
# kwargs (dict): more arguments
##################################################################################


def drain_to_p_00(in_raster, dem):
    """Converts a drainage direction file produced by r.watershed for use by
    TauDem.

    Parameters
    ----------
    in_raster : str
        Name of GRASS drainage direction raster
    dem : str

    """
    import grass.script as gscript
    
    out_raster = in_raster.replace("drain", "drain-p")
    
    expr = "{o} = if( {i}>=1, if({i}==8, 1, {i}+1), null() )".format(
        o=out_raster, i=in_raster)
    
    gscript.raster.mapcalc(expr)
    
    export_raster_00(out_raster, 'Surface_Flow', 'SFW', 'P', str(dem))


def stream_to_src_00(stream, dem):
    """

    Parameters
    ----------
    dem : str or obj
        Path to DEM file
    stream : str
        Name of GRASS stream raster
    """
    
    import grass.script as gscript
    
    out_raster = stream.replace("stream", "str-src")
    
    # All non-zero values to 1
    expr = "{o} = if(isnull({i}), 0, 1)".format(o=out_raster, i=stream)
    gscript.raster.mapcalc(expr)
    
    export_raster_00(out_raster, 'Stream_Pres', 'STPRES', 'SRC', dem)


def watershed_batch_00(dem_path, grass_db_folder, min_basin_size=100):
    """

    Parameters
    ----------
    dem_path : str
        Path to the DEM to import.
    grass_db_folder : str
        path to the root directory to store the GRASS files
    min_basin_size : int
        watershed basin minimum size, in cells. 100 works for 20ft resolution
    """

    # Open or create grass mapset and import dem
    open_location_00(str(dem_path), str(grass_db_folder))
    elev_raster = import_dem_00(str(dem_path))
    
    # Run watershed tool
    watershed_rasters = watershed_00(str(elev_raster), min_basin_size)
    stream = watershed_rasters['stream']
    drain = watershed_rasters['drain']
    
    # Reclassify and export GRASS rasters for use with TauDEM
    stream_to_src_00(stream, dem_path)
    drain_to_p_00(drain, dem_path)
    
    ########### Copied
    # Clean up at the end
    #gsetup.cleanup()
    ###########


# if __name__ == '__main__':
#
#     ### Testing inputs ###
#     in_dem_path = r'D:\Work\Data\CHOWN05\Surface\DSM00_LDR2014' \
#                   r'\CHOWN05_DEM00_LDR2014_D20.tif'
#     gisdb = r'D:\Work\Data\grassdata')
#     location = "chown05"
#     mapset = "mapset_00"
#     grass7bin = r'C:\OSGeo4W64\bin\grass78.bat'
#     ######
#
#     watershed_batch_00(in_dem_path, gisdb, location, mapset, 100)
