#! python3

"""
Don't run this.
"""


def grass_setup_00(gisdb, location, mapset='PERMANENT'):
    """Opens the GRASS mapset.

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

    # Location of GRASS binary
    grass7bin = r'C:\OSGeo4W64\bin\grass78.bat'

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
    if p.returncode!=0:
        sys.exit("ERROR: Issues running GRASS GIS start script"
                 " {cmd}: {error}"
                 .format(cmd=' '.join(startcmd), error=err))
    gisbase = out.strip(os.linesep)

    # set GISBASE environment variable
    os.environ['GISBASE'] = gisbase

    # define GRASS-Python environment
    grass_pydir = os.path.join(gisbase, "etc", "python")
    sys.path.append(grass_pydir)

    # Import GRASS Python bindings
    import grass.script as gscript

    # Launch session
    rcfile = gscript.setup.init(gisbase, gisdb, location, mapset)

    # Example calls
    gscript.message('Current GRASS GIS 7 environment:')
    print(gscript.gisenv())

    gscript.message('Available raster maps:')
    for rast in gscript.list_strings(type='raster'):
        print(rast)

    gscript.message('Available vector maps:')
    for vect in gscript.list_strings(type='vector'):
        print(vect)


def import_dem_00(in_dem_path):
    """

    Parameters
    ----------
    in_dem_path : str
        Path to the DEM

    Returns
    -------
    in_raster : str
        Name of the imported raster
    """
    import os

    import grass.script as gscript

    out_raster = '_'.join(os.path.basename(in_dem_path).split('_')[0:2])

    gscript.run_command('r.in.gdal', input=in_dem_path, output=out_raster)

    return out_raster


def export_raster_00(in_raster, name, prj_path):
    """

    Parameters
    ----------
    in_raster : str
        Name of GRASS raster to export
    name : str
        Model file abbreviation
    out_dir : str
        Path to output group directory
    """
    # TODO: Write function to export the raster to a geotiff file.

    import pathlib

    if name == 'SRC':

    elif name == 'P':



def watershed_00(in_raster_name, threshold):
    """Runs r.watershed

    Parameters
    ----------
    in_raster_name : str
        Name of imported dem file
    threshold : int
        Minimum size, in map cells, of individual watersheds. 100 gives reasonable results for 20ft resolution

    Returns
    -------
    watershed_rasters : dict
        Output rasters {type: name}
    """

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

    # TODO: Run r.watershed. console command: r.watershed elevation=CHOWN05_DEM01@PERMANENT threshold=100
    #  accumulation=CHOWN05_acc tci=CHOWN05_tci spi=CHOWN05_spi drainage=CHOWN05_drain basin=CHOWN05_basin
    #  stream=CHOWN05_stream length_slope=CHOWN05_slplen slope_steepness=CHOWN05_slpstp

    gscript.run_command('r.watershed', input=in_raster_name, threshold=threshold, **watershed_rasters)

    return watershed_rasters


##################################################################################
# mapcalc parameters:
# exp (str): expression
# quiet (bool): true to run quietly
# verbose (bool): true to run verbosely
# overwrite (bool): true to enable overwriting the output
# seed (int): integer to seed the random-number generator for the rand() function
# env (dict): dictionary of environment variables for child process
# kwargs (dict): more arguments
##################################################################################


def drain_to_p_00(in_raster):
    """Converts a drainage direction file produced by r.watershed for use by TauDem.

    Parameters
    ----------
    in_raster : str
        Name of GRASS drainage direction raster
    """


    out_raster = in_raster.replace('drain', 'flowdir')
    # If drain < 1: td = 0. Elif drain = 8: td = 1. Else: td = drain + 1

    expr = "{o} = if({i}<1, null(), if({i}==8, 1, {i}+1))".format(o=out_raster, i=in_raster)

    script.raster.mapcalc(expr)

    export_raster_00(out_raster, 'P')

def stream_to_src_00(stream):
    """

    Parameters
    ----------
    stream :

    Returns
    -------

    """

    out_raster = stream.replace('stream', 'str-src')

    # All non-zero values to 1
    expr = '{o} = if({i}, 1, null())'.format(o=out_raster, i=stream)
    script.raster.mapcalc(expr)

    export_raster_00(out_raster, 'SRC')  # Might need to add more parameters here to get the right file formats


def watershed_batch_00(dem_path, grass_db_folder, grass_location, grass_mapset, min_basin_size=100):
    """

    Parameters
    ----------
    dem_path : str
        path to the DEM to import
    grass_db_folder : str
        path to the root directory to store the GRASS files
    grass_location : str
        name of the subfolder to store this GRASS project
    grass_mapset : str
        name of the mapset
    min_basin_size : int
        watershed basin minimum size, in cells. 100 works for 20ft resolution
    """

    # Set up grass environment and import tif
    grass_setup_00(grass_db_folder, grass_location, grass_mapset)
    elev_raster = import_dem_00(dem_path)

    # Run watershed tool
    watershed_rasters = watershed_00(elev_raster, min_basin_size)
    stream = watershed_rasters['stream']
    drain = watershed_rasters['drain']

    # Reclassify and export GRASS rasters for use with TauDEM
    stream_to_src_00(stream)
    drain_to_p_00(drain)

    ########### Copied
    # Clean up at the end
    #gsetup.cleanup()
    ###########


if __name__=='__main__':

    ### Testing inputs ###
    in_dem_path = r'C:\Users\betha\Work\Data\CHOWN05\Surface\DSM00_LDR2014\CHOWN05_DEM00_LDR2014_D20.tif'
    gisdb = os.path.join(os.path.expanduser("~"), "Work", "grass_test")
    location = "chown05"
    mapset = "mapset_01"

    grass7bin = r'C:\OSGeo4W64\bin\grass78.bat'

    ######


    watershed_batch_00(in_dem_path, gisdb, location, mapset)
