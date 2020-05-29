#!/usr/bin/env python3
"""
Runs GRASS scripts from outside the GRASS interface.




"""


def get_grass_bin_00():

    from pathlib import Path

    #TODO: Get Windows install drive, in case it's not C
    os_drive = 'C:' #PLACEHOLDER
    osd = Path(os_drive)

    # Potential locations for GRASS install:
    dirs = [
        osd / r'Program Files',
        osd / r'OSGeo',
        osd / r'Program Files (x86)',
        #TODO: User folder
    ]

    searchdirs = []
    for dir in [d for d in dirs if d.exists()]:
        searchdirs.extend([p for p in list(dir.iterdir()) if (p.is_dir() and 'GRASS' in p.name)])

    grass_paths = []
    for d in searchdirs:
        grass_paths = list(Path(d).glob('**/grass*.bat'))
        if len(grass_paths) >= 1:
            break

    gb = grass_paths[0]
    return gb


def get_grass_dir_00(grass_bin):
    """ Gets GRASS install location and sets environmental variables.

    Parameters
    ----------
    grass_bin : Path object or str

    Returns
    -------
    gisbase : str
    """

    import os
    import subprocess
    import sys

    # Get grass_base and python path
    # Query GRASS GIS itself for its GISBASE
    basecmd = [str(grass_bin), '--config', 'path']
    try:
        p = subprocess.Popen(basecmd, shell=False,
                             stdout=subprocess.PIPE, stderr=subprocess.PIPE)
        out, err = p.communicate()
    except OSError as error:
        sys.exit("ERROR: Cannot find GRASS GIS start script"
                 " {cmd}: {error}".format(cmd=basecmd[0], error=error))
    if p.returncode != 0:
        sys.exit("ERROR: Issues running GRASS GIS start script"
                 " {cmd}: {error}"
                 .format(cmd=' '.join(basecmd), error=err))
    gisbase = out.decode().strip(os.linesep)

    # Set environment variables
    os.environ['GISBASE'] = gisbase
    os.environ['PATH'] += os.pathsep + os.path.join(gisbase, 'extrabin')
    home = os.path.expanduser("~")
    os.environ['PATH'] += os.pathsep + os.path.join(home, '.grass7', 'addons', 'scripts')

    return gisbase




def grass_setup_00(grass_db, grass_bin):
    """Gets the GRASS install dir and sets environment variables

    Parameters
    ----------
    grass_db : str or Path obj
    grass_bin : str or Path obj

    Returns
    -------

    """
    from pathlib import Path
    import os
    import sys
    import subprocess

    grass_db = Path(str(grass_db_path))
    dem = Path(str(dem_path))

    grass_bin = get_grass_bin_00()

    # Get grass_base and python path
    # Query GRASS GIS itself for its GISBASE
    basecmd = [str(grass_bin), '--config', 'path']
    try:
        p = subprocess.Popen(basecmd, shell=False,
                             stdout=subprocess.PIPE, stderr=subprocess.PIPE)
        out, err = p.communicate()
    except OSError as error:
        sys.exit("ERROR: Cannot find GRASS GIS start script"
                 " {cmd}: {error}".format(cmd=basecmd[0], error=error))
    if p.returncode != 0:
        sys.exit("ERROR: Issues running GRASS GIS start script"
                 " {cmd}: {error}"
                 .format(cmd=' '.join(basecmd), error=err))
    gisbase = out.decode().strip(os.linesep)

    # Set environment variables
    os.environ['GISBASE'] = gisbase
    os.environ['PATH'] += os.pathsep + os.path.join(gisbase, 'extrabin')
    home = os.path.expanduser("~")
    os.environ['PATH'] += os.pathsep + os.path.join(home, '.grass7', 'addons', 'scripts')

    if not grass_db.exists():
        grass_db.mkdir(parents=True)
    os.environ['GISDBASE'] = str(grass_db)

    # Add GRASS python to path
    grass_py = os.path.join(gisbase, "etc", "python")
    sys.path.append(gisbase)
    sys.path.append(grass_py)

    # Create location name from dem filename
    name_parts = dem.stem.split('_')
    loc_name = '_'.join(name_parts[0:2])

    # Create location
    loc_path = grass_db / loc_name
    if not loc_path.exists():
        startcmd = [grass_bin_path, '-c', dem_path, '-e', str(loc_path)]
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

    # Start session
    import grass.script as gscript
    import grass.script.setup as gsetup

    rc_file = gsetup.init(grass_base, str(grass_db), loc_name, 'PERMANENT')

    return rc_file


def new_location_00(dem_path, grass_db_path):
    """Creates a new GRASS location and imports the dem

    TODO: Move location and import steps here

    Parameters
    ----------
    dem_path
    grass_db_path

    Returns
    -------

    """
    pass


    # create location name from dem filename
    name_parts = dem.stem.split('_')
    loc_name = '_'.join(name_parts[0:2])

    # Create location
    loc_path = grass_db / loc_name
    if not loc_path.exists():
        startcmd = [grass_bin_path, '-c', dem_path, '-e', str(loc_path)]
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


def watershed_ext_00(dem_path, resolution, grass_db_path,
                     grass_bin_path, min_basin=None):
    """Runs r.watershed on a single DEM and exports P and SRC files.

    Parameters
    ----------
    dem_path : str
        Path to the DEM to import
    resolution : int or str
        Resolution of the DEM (20, 10, 5...)
    grass_db_path : str or Path obj
        Path to grass data root folder
    grass_bin_path : str or Path obj #TODO: Make this optional
        Path to grass7*.bat
        If standalone GRASS, default is `C:\Program Files\GRASS GIS 7.8\grass78.bat`
        If installed with OSGEO, default is `C:\OSGeo4W64\bin\grass78.bat`
    min_basin : int or str, optional
        Minimum size, in cells, for a sub-basin
        Depends on resolution. Leave blank to select automatically.

    Returns
    -------
    dict
        Paths to exported files `p` and `src`
    """
    from pathlib import Path
    import os
    import sys
    import subprocess

    grass_db = Path(str(grass_db_path))
    dem = Path(str(dem_path))

    ######################################################
    #TODO: Replace this section with call to `grass_setup_00`

    # Get grass_base and python path
    # query GRASS GIS itself for its GISBASE

    basecmd = [grass_bin_path, '--config', 'path']
    try:
        p = subprocess.Popen(basecmd, shell=False,
                             stdout=subprocess.PIPE, stderr=subprocess.PIPE)
        out, err = p.communicate()
    except OSError as error:
        sys.exit("ERROR: Cannot find GRASS GIS start script"
                 " {cmd}: {error}".format(cmd=basecmd[0], error=error))
    if p.returncode != 0:
        sys.exit("ERROR: Issues running GRASS GIS start script"
                 " {cmd}: {error}"
                 .format(cmd=' '.join(basecmd), error=err))
    grass_base = out.decode().strip(os.linesep)

    # set environment variables
    os.environ['GISBASE'] = grass_base
    os.environ['PATH'] += os.pathsep + os.path.join(grass_base, 'extrabin')
    home = os.path.expanduser("~")
    os.environ['PATH'] += os.pathsep + os.path.join(home, '.grass7', 'addons', 'scripts')

    if not grass_db.exists():
        grass_db.mkdir(parents=True)
    os.environ['GISDBASE'] = str(grass_db)

    # add GRASS python to path
    grass_py = os.path.join(grass_base, "etc", "python")
    sys.path.append(grass_base)
    sys.path.append(grass_py)

    # create location name from dem filename
    name_parts = dem.stem.split('_')
    loc_name = '_'.join(name_parts[0:2])

    # Create location
    loc_path = grass_db / loc_name
    if not loc_path.exists():
        new_loc_cmd = [grass_bin_path, '-c', dem_path, '-e', str(loc_path)]
        try:
            p = subprocess.Popen(new_loc_cmd, shell=False,
                                 stdout=subprocess.PIPE, stderr=subprocess.PIPE)
            out, err = p.communicate()
        except OSError as error:
            sys.exit("ERROR: Cannot find GRASS GIS start script"
                     " {cmd}: {error}".format(cmd=new_loc_cmd[0], error=error))
        if p.returncode != 0:
            sys.exit("ERROR: Issues running GRASS GIS start script"
                     " {cmd}: {error}"
                     .format(cmd=' '.join(new_loc_cmd), error=err))

    #######################################################################

    # Set environmental variables for location and mapset

    os.environ['GRASS_GUI'] = "text"



    # Start session with location
    import grass.script as gscript
    import grass.script.setup as gsetup
    import gr_watershed_00 as grw

    gisrc = gsetup.init(grass_base, str(grass_db), loc_name, 'PERMANENT')

    os.environ['GISRC'] = gisrc


    # Open location

    mapset_path = loc_path / 'PERMANENT'

    startcmd = [grass_bin_path, str(mapset_path)]
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

    #########################################################################

    gscript.message('Available raster maps:')
    for rast in gscript.list_strings(type="rast", mapset="PERMANENT"):
        print(rast)

    #loc_rasts = gscript.list_strings('raster')

    # loc_rasts = gscript.core.list_strings(type='rast', mapset='PERMANENT')
    # loc_rasts = gscript.run_command('g.list', type="rast")


    # Select minimum basin threshold if not specified:
    if min_basin is None:
        thresholds = {'20': 100, '10': 500, '5': 1200}
        if str(resolution) in thresholds.keys():
            min_basin = thresholds[str(resolution)]
        else:
            print("Minimum basin size required")

    # # Import DEM
    grs_dem = '_'.join(name_parts[0:2])

    # Check whether the raster has already been imported:
    # if grs_dem + "@PERMANENT" not in loc_rasts:
    #     print('Run r.in.gdal')
    #     #TEST: This step is already in grw.dem_to_src_00, but doesn't work when called from here
    #     gscript.run_command('r.in.gdal', input=dem_path, output=dem_name)

    gscript.run_command('r.in.gdal', input=dem_path, output=grs_dem, overwrite=True)
    # Set region to match imported raster
    gscript.run_command('g.region', raster=grs_dem)

    # Run r.watershed
    watershed_rasters = grw.watershed_00(str(grs_dem), min_basin)
    stream = watershed_rasters['stream']
    drain = watershed_rasters['drainage']

    # Reclassify and export GRASS rasters for use with TauDEM
    src = grw.stream_to_src_00(stream, dem_path)
    #
    p = grw.drain_to_p_00(drain, dem_path)
    #
    return {'src': src, 'p': p}


    # gscript.run_command('r.in.gdal', input=str(dem_path), output=dem_ras, overwrite=True)
    # gscript.run_command('r.external', input=str(dem_path), output=dem_ras, overwrite=True)
    #
    # gscript.run_command('g.region', raster=dem_ras)

    # Run r.watershed:
    #out_files = grw.dem_to_src_00(dem_path, min_basin)

    #return out_files

def run_grass_script_00(mapset_path, script_path, *args):
    """Runs a GRASS module without opening GRASS.

    Parameters
    ----------
    mapset_path : str
    script_path : str
    args : list

    Returns
    -------

    """
    import sys
    import subprocess

    grass_bin_path = str(get_grass_bin_00())

    cmd = [grass_bin_path, mapset_path, "--exec", "python", script_path, args]
    try:
        p = subprocess.Popen(cmd, shell=False,
                             stdout=subprocess.PIPE, stderr=subprocess.PIPE)
        out, err = p.communicate()
    except OSError as error:
        sys.exit("ERROR: Cannot find GRASS GIS start script"
                 " {cmd}: {error}".format(cmd=cmd[0], error=error))
    if p.returncode != 0:
        sys.exit("ERROR: Issues running GRASS GIS start script"
                 " {cmd}: {error}"
                 .format(cmd=' '.join(cmd), error=err))


if __name__ == "__main__":
    # import doctest
    # doctest.testfile("test.txt", verbose=True)
    grass_base = r'C:\Program Files\GRASS GIS 7.8'
    dem_path = r'D:\Work\Data\CHOWN05_TEST03\Surface\DSM00_LDR2014\CHOWN05_DEM00_LDR2014_D20.tif'
    resolution = 20
    grass_db_path = r'D:\Work\Data\grassdata05'
    mapset = r'D:\Work\Data\grassdata05\CHOWN05_DEM00\PERMANENT'
    grass_bin = r'C:\Program Files\GRASS GIS 7.8\grass78.bat'
    min_basin = 100
    #watershed_script_path = r'D:\Work\scripts\grass_scripts\gr_watershed_00.py'

    #watershed_ext_00(dem_path, resolution, grass_db_path, grass_bin, min_basin)

    run_grass_script_00(mapset, "--exec", "python", r'D:\Work\scripts\grass_scripts\grass_test.py')
