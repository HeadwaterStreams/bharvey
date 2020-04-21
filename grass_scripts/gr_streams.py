#!/usr/bin/env python3
#
#########################################################################
#
# MODULE:       Watershed-export
#
# AUTHOR(S):    bharvey2
#
# PURPOSE:      Run r.watershed and export files for TauDEM
#
# DATE:         Tue Apr 21 09:26:38 2020
#
#########################################################################

#%module
#% description: Imports a DEM, runs r.watershed, reclassifies, and exports tifs
#% keyword:
#%end
#%option G_OPT_R_INPUT
#% key: dem_path
#% description: Absolute path to the DEM to import
#%end
#%option G_OPT_R_INPUT
#% key: resolution
#% description: Length of a raster cell, in feet. Ex: 20, 10, 5...
#%end
#%option G_OPT_R_INPUT
#% key: threshold
#% description: Min basin size, in cells. Leave blank to select automatically.
#%end

import sys
from pathlib import Path

import grass.script as gscript
# from grass.exceptions import CalledModuleError

##############################################################
# Setup Functions
# Skip if running from within GRASS
# None of these work yet
##############################################################


def grass_environment_00(grass_bin=r'C:\Program Files\GRASS GIS 7.8\grass78.bat'):
    """Get and/or set GRASS paths and environmental variables
    
    Parameters
    ----------
    grass_bin : str
        Path to GRASS binary.

    Returns
    -------
    gisbase : str
    """
    import os
    import sys
    import subprocess

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


def grass_setup_00(gisdb, location):
    """Start GRASS and open the specified mapset.

    Parameters
    ----------
    gisdb : str
        Path to the GRASS database.
    location : str
        Name of the GRASS location.
    mapset : str
        Name of the mapset. One called PERMANENT is automatically created.
    """
    
    import os
    import sys
    import subprocess

    # Location of GRASS binary
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
    
    # Launch session
    rcfile = gscript.setup.init(gisbase, gisdb, location)
    
    # # Example calls
    gscript.message('Current GRASS GIS 7 environment:')
    print(gscript.gisenv())


def grass_start_00():
    """Select and run required GRASS setup commands"""
    pass


def grass_stop_00():
    """Close GRASS and clean up temporary files"""
    pass

    # gsetup.cleanup()


##############################################################
# GRASS tools
# These work if run from within GRASS
##############################################################

def import_dem_00(dem_path):
    """Import the DEM as a GRASS raster and set the region to match it

    Parameters
    ----------
    dem_path : str
        Path to the DEM

    Returns
    -------
    out_raster : str
        Name of the imported raster
    """

    name_parts = Path(str(dem_path)).name.split('_')
    out_raster = '_'.join(name_parts[0:2])

    # Import the DEM if it hasn't already been imported
    # It would probably be easier to add --overwrite?
    # try:
    gscript.run_command('r.in.gdal', input=str(dem_path),
                            output=out_raster, overwrite=True)
    # except CalledModuleError:
    #     pass

    # Set computational region
    gscript.run_command('g.region', raster=out_raster)

    return out_raster


def watershed_00(in_raster_name, resolution, threshold=None):
    """Run r.watershed

    Parameters
    ----------
    in_raster_name : str
        Name of imported dem file
    resolution : int
        Size of a map cell.
    threshold : int
        (Optional) Minimum size, in map cells, of individual watersheds. If
        not specified, choose based on resolution.

    Returns
    -------
    watershed_rasters : dict
        Output rasters {type: name}
    """

    thresholds = {
        '20': 100,
        '10': 500,
        '5': 1200,
    }

    huc = in_raster_name.split('_')[0]
    num = in_raster_name[-2:]

    # Raster names
    watershed_rasters = {
        'elevation': in_raster_name,
        'accumulation': "{h}_acc_{n}".format(h=huc, n=num),
        'tci': "{h}_tci_{n}".format(h=huc, n=num),
        'spi': "{h}_spi_{n}".format(h=huc, n=num),
        'drainage': "{h}_drain_{n}".format(h=huc, n=num),
        'basin': "{h}_basin_{n}".format(h=huc, n=num),
        'stream': "{h}_stream_{n}".format(h=huc, n=num),
        'length_slope': "{h}_slplen_{n}".format(h=huc, n=num),
        'slope_steepness': "{h}_slpstp_{n}".format(h=huc, n=num)
    }

    # Get threshold
    if threshold is None:
        if str(resolution) in thresholds.keys():
            threshold = thresholds[str(resolution)]
        else:
            threshold = 100

    gscript.core.run_command('r.watershed', threshold=threshold, overwrite=True,
                             **watershed_rasters)

    return watershed_rasters


def drain_to_p_00(in_raster, dem):
    """Convert a drainage direction file produced by r.watershed for use by
    TauDem.

    Parameters
    ----------
    in_raster : str
        Name of GRASS drainage direction raster
    dem : str

    """

    out_raster = in_raster.replace("drain", "drainp")

    expr = "{o} = if( {i}>=1, if({i}==8, 1, {i}+1), null() )".format(
        o=out_raster, i=in_raster)

    gscript.raster.mapcalc(expr, overwrite=True)

    p_path = export_raster_00(out_raster, 'Surface_Flow', 'SFW', 'P', str(dem))

    return p_path


def stream_to_src_00(stream, dem):
    """

    Parameters
    ----------
    dem : str or obj
        Path to DEM file
    stream : str
        Name of GRASS stream raster
    """

    out_raster = stream.replace("stream", "strsrc")

    # All non-zero values to 1
    expr = "{o} = if(isnull({i}), 0, 1)".format(o=out_raster, i=stream)
    gscript.raster.mapcalc(expr, overwrite=True)

    src_path = export_raster_00(out_raster, 'Stream_Pres', 'STPRES', 'SRC', dem)

    return src_path


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

    dem = Path(dem_path)
    dsm = dem.parent
    prj = dsm.parent.parent

    group_parent_path = prj.joinpath(group_parent_name)

    grps = group_parent_path.glob(group_str + '*')

    if grps:
        grpnos = []
        for grp in grps:
            grpno = grp.name.split("_")[0][-2:]
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

    gscript.run_command('r.out.gdal', input=in_raster, output=out_path,
                        format="GTiff", type="Int16",
                        createopt="COMPRESS=LZW,PREDICTOR=2,BIGTIFF=YES",
                        nodata=-32768)
    return str(out_path)


##################################
# Combined functions
##################################

def dem_to_src_and_p(dem_path, resolution, threshold=None):
    """Run import, watershed, mapcalc, and export tools
    """

    output_paths = []

    # Import dem
    elev_raster = import_dem_00(str(dem_path))

    # Run watershed tool
    watershed_rasters = watershed_00(str(elev_raster), resolution, threshold)
    stream = watershed_rasters['stream']
    drain = watershed_rasters['drainage']

    # Reclassify and export GRASS rasters for use with TauDEM
    src = stream_to_src_00(stream, dem_path)
    output_paths.append(src)

    p = drain_to_p_00(drain, dem_path)
    output_paths.append(p)

    # Print new file locations
    print(output_paths, sep='\n')


def watershed_batch_00(dem_paths, grass_db_folder, resolution,
                       threshold=None): #FIXME
    """

    Parameters
    ----------
    dem_paths : list
        Paths to the DEMs to import
    grass_db_folder : str
        Path to the root directory to store the GRASS files
    resolution : int
        Length of a raster cell, in feet
    threshold : int
        (Optional) Watershed basin minimum size, in cells
    """


    grass_start_00()

    for dem in dem_paths:
        # Import DEM, creating a new location
        elev_raster = import_dem_00(str(dem))

        # Run watershed tool
        watershed_rasters = watershed_00(str(elev_raster), resolution, threshold)
        stream = watershed_rasters['stream']
        drain = watershed_rasters['drain']

        # Reclassify and export GRASS rasters for use with TauDEM
        stream_to_src_00(stream, dem)
        drain_to_p_00(drain, dem)


    grass_stop_00()


def main():
    """To run as a module from the GRASS user interface

    Skips setup functions and runs import, watershed, mapcalc, and export tools
    """

    options, flags = gscript.parser()
    dem_path = options['dem_path']
    resolution = options['resolution']
    threshold = options['threshold']

    dem_to_src_and_p(dem_path, resolution, threshold)


if __name__ == "__main__":
    sys.exit(main())
