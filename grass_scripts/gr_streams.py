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
    os.environ['GISBASE'] = gisdb

    # define GRASS-Python environment
    grass_pydir = os.path.join(gisdb, "etc", "python")
    sys.path.append(grass_pydir)

    # Import GRASS Python bindings
    import grass.script as gs

    # Launch session
    rcfile = gs.setup.init(gisbase, gisdb, location, mapset)

    # # Example calls
    # gs.message('Current GRASS GIS 7 environment:')
    # print(gs.gisenv())
    #
    # gs.message('Available raster maps:')
    # for rast in gs.list_strings(type='raster'):
    #     print(rast)
    #
    # gs.message('Available vector maps:')
    # for vect in gs.list_strings(type='vector'):
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
    import os

    import grass.script as gs

    out_raster = '_'.join(os.path.basename(dem_path).split('_')[0:2])

    # Import DEM
    gs.run_command('r.in.gdal', input=dem_path, output=out_raster)

    # Set computational region
    gs.run_command('g.region', raster=out_raster)

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

    import grass.script as gs

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
    out_file_name = "{}{}_{}.tif".format(name, new_group_no, dem.name.split("_")[1])
    out_path = new_group.joinpath(out_file_name)

    # CLI command: r.out.gdal -c --overwrite input=in_raster
    # output=out_path format=GTiff type=Int16
    # createopt=COMPRESS=LZW,PREDICTOR=2,BIGTIFF=YES nodata=-32768

    gs.run_command('r.out.gdal', input=in_raster, output=out_path, format="GTiff", type="Int16", createopt="COMPRESS=LZW,PREDICTOR=2,BIGTIFF=YES", nodata=-32768)


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

    import grass.script as gs

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


    gs.run_command('r.watershed', input=in_raster_name, threshold=threshold, **watershed_rasters)

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


def drain_to_p_00(in_raster, dem):
    """Converts a drainage direction file produced by r.watershed for use by TauDem.

    Parameters
    ----------
    in_raster : str
        Name of GRASS drainage direction raster
    dem : str or obj

    """
    import pathlib.Path

    import grass.script as gs

    out_raster = in_raster.replace("drain", "drain-p")

    expr = "{o} = if( {i}>=1, if({i}==8, 1, {i}+1), null() )".format(o=out_raster, i=in_raster)

    gs.raster.mapcalc(expr)

    export_raster_00(out_raster, 'Surface_Flow', 'SFW', 'P', dem)


def stream_to_src_00(stream, dem):
    """

    Parameters
    ----------
    dem : str or obj
        Path to DEM file
    stream : str
        Name of GRASS stream raster
    """





    out_raster = stream.replace("stream", "str-src")

    # All non-zero values to 1
    expr = "{o} = if(isnull({i}), 0, 1)".format(o=out_raster, i=stream)
    gs.raster.mapcalc(expr)


    export_raster_00(out_raster, 'Stream_Pres', 'STPRES', 'SRC', dem)


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
    stream_to_src_00(stream, dem_path)
    drain_to_p_00(drain, dem_path)

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
