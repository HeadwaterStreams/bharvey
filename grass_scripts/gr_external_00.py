#! C:\Apps\GRASS78\Python37\python.exe
"""
Runs GRASS scripts from outside the GRASS user interface.

You may need to edit paths, including the first line, which is the path to the Python interpreter used by GRASS.



    %GISBASE%
    %GISBASE%\\bin
    %GISBASE%\\scripts
    %GISBASE%\\lib
    %GISBASE%\\extrabin
    path to GRASS data location

"""


def get_grass_bin_00():
    from pathlib import Path

    home = Path.home()
    osd = Path(home.anchor)

    # Locations to search for GRASS
    dirs = [
        osd / r'Program Files',
        osd / r'Apps',
        home / r'Apps',
        home,
        osd
    ]

    searchdirs = []
    for sd in [d for d in dirs if d.exists()]:
        searchdirs.extend([p for p in list(sd.iterdir()) if (p.is_dir() and 'grass' in p.name.lower())])

    grass_paths = []
    for d in searchdirs:
        grass_paths = list(Path(d).glob('**/grass*.bat'))
        if len(grass_paths) >= 1:
            break

    gb = grass_paths[0]
    return str(gb)


def get_grass_dir_00(grass_bin):
    """ Finds GRASS install location.

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
                             stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True)
        out, err = p.communicate()
    except OSError as error:
        sys.exit("ERROR: Cannot find GRASS GIS start script"
                 " {cmd}: {error}".format(cmd=basecmd[0], error=error))
    if p.returncode != 0:
        sys.exit("ERROR: Issues running GRASS GIS start script"
                 " {cmd}: {error}"
                 .format(cmd=' '.join(basecmd), error=err))
    gisbase = out.strip(os.linesep)

    # Set environment variables and add paths
    os.environ['GISBASE'] = gisbase
    home = os.path.expanduser("~")
    os.environ['PATH'] += ";{};{};{}".format(os.path.join(gisbase, 'bin'), os.path.join(gisbase, 'extrabin'), os.path.join(gisbase,'lib')) 
    
    sys.path.append(os.path.join(home, '.grass7', 'addons', 'scripts'))    
    sys.path.append(os.path.join(gisbase, 'scripts'))
    sys.path.append(os.path.join(gisbase, 'etc', 'python'))
    
    return gisbase


def set_grass_envs_00(grass_bin=None, gisbase=None):
    """Sets environment variables.

    Parameters
    ----------
    grass_bin : str or Path obj, optional
    gisbase : str or Path obj, optional
        Path to GRASS install dir.

    Returns
    -------

    """
    import os
    import sys
    from pathlib import Path

    # Get GRASS binary and install dir paths
    if grass_bin is None:
        grass_bin = get_grass_bin_00()
    if gisbase is None:
        gisbase = get_grass_dir_00(grass_bin)

    base = Path(gisbase)
    # Add GRASS python dirs to path
    grass_py = os.path.join(gisbase, "etc", "python")
    
    # Find GRASS or OSGEO Python env
    # if os.environ['GRASS_PYTHON'] == None:
    #    dirs = [base, base.parent.parent]
    #    for dir in [d for d in dirs if d.exists()]:
    #        searchdirs.extend([p for p in list(dir.iterdir()) if (p.is_dir() and 'Python' in p.name)])
    
    grass_interpreter = os.path.join(gisbase, "Python37", "python.exe")  # TODO: Replace with a search so other versions will work
    os.environ['GRASS_PYTHON'] = grass_interpreter
    
    sys.path.append(gisbase)
    sys.path.append(grass_py)
    sys.path.append(grass_interpreter)

    return grass_interpreter


# def location_setup():
#
#     import sys
#     import subprocess
#     from pathlib import Path
#
#     # Create DB, Location, and Mapset
#
#     grass_db = Path(str(grass_db_path))
#     if not grass_db.exists():
#         grass_db.mkdir(parents=True)
#     os.environ['GISDBASE'] = str(grass_db)
#
#     # Create location name from dem filename
#     dem = Path(str(dem_path))
#     name_parts = dem.stem.split('_')
#     loc_name = '_'.join(name_parts[0:2])
#
#     # Create location
#     loc_path = grass_db / loc_name
#     if not loc_path.exists():
#         loc_cmd = [str(grass_bin), '-c', dem_path, '-e', str(loc_path)]
#         try:
#             p_loc = subprocess.Popen(loc_cmd, shell=False,
#                                      stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True)
#             out, err = p_loc.communicate()
#         except OSError as error:
#             sys.exit("ERROR: Cannot find GRASS GIS start script"
#                      " {cmd}: {error}".format(cmd=loc_cmd[0], error=error))
#         if p_loc.returncode != 0:
#             sys.exit("ERROR: Issues running GRASS GIS start script"
#                      " {cmd}: {error}"
#                      .format(cmd=' '.join(loc_cmd), error=err))
#
#     # Start session
#     import grass.script as gscript
#     import grass.script.setup as gsetup
#
#     rc_file = gsetup.init(grass_base, str(grass_db), loc_name, 'PERMANENT')
#
#     return rc_file


def new_location_00(dem_path, grass_db_path, grass_bin_path):
    """Creates a new GRASS location and imports the dem

    TODO: Move location and import steps here

    Parameters
    ----------
    dem_path
    grass_db_path

    Returns
    -------

    """

    import subprocess
    import sys
    from pathlib import Path

    dem = Path(dem_path)

    # create location name from dem filename
    name_parts = dem.stem.split('_')
    loc_name = '_'.join(name_parts[0:2])

    # Create location
    loc_path = grass_db_path / loc_name
    if not loc_path.exists():
        startcmd = [grass_bin_path, '-c', dem_path, '-e', str(loc_path)]
        try:
            p = subprocess.Popen(startcmd, shell=False,
                                 stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True)
            out, err = p.communicate()
        except OSError as error:
            sys.exit("ERROR: Cannot find GRASS GIS start script"
                     " {cmd}: {error}".format(cmd=startcmd[0], error=error))
        if p.returncode != 0:
            sys.exit("ERROR: Issues running GRASS GIS start script"
                     " {cmd}: {error}"
                     .format(cmd=' '.join(startcmd), error=err))


def run_grass_script_cmd_00(mapset_path, script_path, grass_bin_path=None, options=None):
    """Runs a script in GRASS

    Parameters
    ----------
    mapset_path : str
    script_path : str
    grass_bin_path : str, optional
    options : str, optional
        Options for the GRASS tool

    Returns
    -------

    """
    import sys
    import subprocess

    if grass_bin_path is None:
        grass_bin_path = get_grass_bin_00()
    set_grass_envs_00(grass_bin=grass_bin_path)

    # cmd = [grass_bin_path, mapset_path, "--exec", "python", script_path]
    # if options != None:
    #     cmd.append(options)
    cmd = '"{g}" "{m}" --exec python "{s}" {o}'.format(g=grass_bin_path, m=mapset_path, s=script_path, o=options)
    try:
        p = subprocess.Popen(cmd, shell=True,
                             stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True)
        out, err = p.communicate()
    except OSError as error:
        sys.exit("ERROR: Cannot find GRASS GIS start script"
                 " {cmd}: {error}".format(cmd=cmd[0], error=error))
    if p.returncode != 0:
        sys.exit("ERROR: Issues running GRASS GIS start script"
                 " {cmd}: {error}"
                 .format(cmd=' '.join(cmd), error=err))


def run_grass_script_py_00():
    """"""
    pass


def watershed_ext_00(dem_path, dem_resolution, grass_data_path,
                     grass_bin_path=None, min_basin_size=None):
    """Runs r.watershed on a single DEM and exports P and SRC files.

    Parameters
    ----------
    dem_path : str
        Path to the DEM to import
    dem_resolution : int or str
        Resolution of the DEM (20, 10, 5...)
    grass_data_path : str or Path obj #TODO: Make this optional and add an if statement to use the default path
        Path to grass data root folder
    grass_bin_path : str or Path obj, optional
        Path to grass7*.bat
    min_basin_size : int or str, optional
        Minimum size, in cells, for a sub-basin.
        Leave blank to select automatically based on `dem_resolution`.

    Returns
    -------
    dict
        Paths to exported files `p` and `src`
    """
    from pathlib import Path
    import os
    import sys
    import subprocess

    gbin = get_grass_bin_00()
    gbase = get_grass_dir_00(gbin)
    gpy = set_grass_envs_00(gbin, gbase)

    grass_db = Path(str(grass_data_path))
    dem = Path(str(dem_path))

    # create location name from dem filename
    name_parts = dem.stem.split('_')
    loc_name = '_'.join(name_parts[0:2])
    loc_path = grass_db / loc_name

    # Create grass_db folder if it doesn't exist
    if not grass_db.exists():
        grass_db.mkdir(parents=True)
    os.environ['GISDBASE'] = str(grass_db)

    # Create location if it doesn't exist
    if not loc_path.exists():
        new_loc_cmd = [grass_bin_path, '-c', dem_path, '-e', str(loc_path)]
        try:
            p1 = subprocess.Popen(new_loc_cmd, shell=False,
                                  stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True)
            out, err = p1.communicate()
        except OSError as error:
            sys.exit("ERROR: Cannot find GRASS GIS start script"
                     " {cmd}: {error}".format(cmd=new_loc_cmd[0], error=error))
        if p1.returncode != 0:
            sys.exit("ERROR: Issues running GRASS GIS start script"
                     " {cmd}: {error}"
                     .format(cmd=' '.join(new_loc_cmd), error=err))

    # =============================================================================


    # Start session with location
    import grass.script as gscript
    from grass.script import setup
    import gr_watershed_00 as grw

    gisrc = setup.init(str(gbase), str(grass_db), str(loc_name), 'PERMANENT')

    os.environ['GISRC'] = gisrc

    # TEST PRINT:
    gscript.message('Current GRASS GIS 7 environment')
    print(gscript.gisenv())

    # gscript.message('Available raster maps:')
    # for rast in gscript.list_strings('raster'):
    #     print(rast)


    # Open location
    mapset_path = loc_path / 'PERMANENT'




    # Select minimum basin threshold if not specified:
    if min_basin_size is None:
        thresholds = {'20': 100, '10': 500, '5': 1200}
        if str(dem_resolution) in thresholds.keys():
            min_basin_size = int(thresholds[str(dem_resolution)])
        else:
            print("Minimum basin size required")




    # # Import DEM
    grs_dem = '_'.join(name_parts[0:2])
    # Check whether the raster has already been imported:
    # if grs_dem + "@PERMANENT" not in loc_rasts:    #
    #     gscript.run_command('r.in.gdal', input=dem_path, output=grs_dem)
    # # Set region to match imported raster
    # gscript.run_command('g.region', raster=grs_dem)
    #
    # # Run r.watershed
    # watershed_rasters = grw.watershed_00(str(grs_dem), min_basin)
    # stream = watershed_rasters['stream']
    # drain = watershed_rasters['drainage']
    #
    # # Reclassify and export GRASS rasters for use with TauDEM
    # src = grw.stream_to_src_00(stream, dem_path)
    # #
    # p = grw.drain_to_p_00(drain, dem_path)
    # #
    # return {'src': src, 'p': p}

    # gscript.run_command("r.in.gdal", input=str(dem_path), output=grs_dem, overwrite=True)
    # gscript.run_command('g.region', raster=grs_dem)

    gscript.run_command("r.in.gdal", flags='e', input=str(dem_path), output=str(grs_dem))

    # Run entire dem to src process:
    #out_files = grw.dem_to_src_00(dem_path, min_basin)
    #gscript.setup.finish()
    #return out_files
    
    

    # TEST Try batch running via Popen instead?
    # opts = "dem={},threshold={}".format(dem_path, min_basin)
    # run_grass_script_00(str(mapset_path), r'D:\Work\scripts\grass_scripts\gr_watershed_00.py', str(gbin), opts)
    # return


if __name__ == "__main__":
    grassbin = get_grass_bin_00()
    gisbase = get_grass_dir_00(grassbin)

    db_path = r'D:\Work\Data\grassdata05'
    mapset = db_path + r'\CHOWN05_DEM00\PERMANENT'

    dem_path = r'D:\Work\Data\CHOWN05_TEST03\Surface\DSM00_LDR2014\CHOWN05_DEM00_LDR2014_D20.tif'
    resolution = 20
    min_basin = 100

    watershed_script_path = r'D:\Work\scripts\grass_scripts\gr_watershed_00.py'

    watershed_ext_00(dem_path, resolution, db_path, grassbin, min_basin)

    # run_grass_script_00(mapset, "--exec", "python", r'D:\Work\scripts\grass_scripts\grass_test.py')
