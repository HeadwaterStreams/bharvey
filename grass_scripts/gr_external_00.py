#!/usr/bin/env python3
"""
Runs GRASS tools from outside the GRASS user interface.

    Because of problems with running grass modules from Python outside of the GRASS interface, this script sets all the necessary
    variables and then sends a command to the terminal to run GRASS with another module instead of directly working with GRASS.
    This way the two scripts can be run by different Python installations.

    WARNING: I have not tested this script but `geomorphons_ext_00` definitely does not work yet.

"""


def get_grass_bin_00():
    from pathlib import Path

    home = Path.home()
    osd = Path(home.anchor)

    # Locations to search for GRASS
    search_dirs = [
        osd / r'Program Files\QGIS 3.10\bin',
        osd / r'Program Files\GRASS78',
        home / r'Apps\GRASS78',
        osd / r'OSGeo4W64', # FIXME: Where is the grass7*.bat file located in the OsGeo folder?
    ]


    # more_dirs = [
    #     osd / r'Program Files',
    #     osd / r'Apps',
    #     home / r'Apps',
    #     #home,
    #     #osd
    # ]


    # for sd in [d for d in dirs if d.exists()]:
    #     # sdl = list(sd.iterdir())
    #     # for p in sdl:
    #     #     if (p.is_dir() and 'grass' in p.name.lower()):
    #     #         searchdirs.append(p)
    #
    #     searchdirs.extend([p for p in list(sd.rglob("*")) if (p.is_dir() and 'grass' in p.name.lower())]) #FIXME: Misses GRASS7.6 installed in OSGeo

    grass_paths = []
    for d in search_dirs:
        if d.exists():
            grass_paths = list(Path(d).glob('**/grass*.bat'))
            if len(grass_paths) >= 1:
                break

    gb = grass_paths[0]
    return str(gb)


def run_command_00(command, msg, err_msg, grass_bin=None):
    """

    Parameters
    ----------
    grass_bin: str or Path obj, optional
        Path to grass78.bat
    command: str
        Command to run.
    err_msg: str
        Error message.
    msg: str
        Message to print on success.

    Returns
    -------
    output: dict
        Command output and files created, if any.

    """

    import subprocess
    import sys

    if grass_bin == None:
        grass_bin = get_grass_bin_00()

    cmd = '"{g}" {c}'.format(g=grass_bin, c=command)
    try:
        p = subprocess.Popen(cmd, shell=False,
                             stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True)
        out, err = p.communicate()
    except OSError as error:
        sys.exit("ERROR: Cannot find GRASS GIS start script"
                 " {cmd}: {error}".format(cmd=cmd[0], error=error))
    if p.returncode != 0:
        sys.exit("{e}"
                 " {cmd}: {error}"
                 .format(e=err_msg, cmd=' '.join(cmd), error=err))
    else:
        sys.exit(msg)

    #TODO: return dictionary w/ paths to any files that were created.


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

    # TODO: Replace this block with a call to `run_command_00`
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

    # Get GRASS binary and install dir paths
    if grass_bin is None:
        grass_bin = get_grass_bin_00()
    if gisbase is None:
        gisbase = get_grass_dir_00(grass_bin)

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

    #TODO: Set GRASS_ADDON_PATH to the script folder.

    return grass_interpreter


def geomorphon_ext_00(dem_path, grass_data_path, script_path,
                       grass_bin=None):
    """Runs geomorphon tools on a single DEM.


    Parameters
    ----------
    dem_path : str
        Path to the DEM to import
    grass_data_path : str or Path obj
        Path to grass data root folder
    script_path : str or Path obj #TODO: Make this optional, it should be in the same folder as this script.
        Path to `gr_geomorphon_00.py`
    grass_bin : str or Path obj, optional
        Path to grass7*.bat

    Returns
    -------
    dict
        Paths to exported files `p` and `src`
    """
    from pathlib import Path
    import os

    if grass_bin == None:
        grass_bin = get_grass_bin_00()
    gbase = get_grass_dir_00(grass_bin)
    #gpy = set_grass_envs_00(gbin, gbase)

    grass_db = Path(str(grass_data_path))
    dem = Path(str(dem_path))
    os.environ['GRASS_ADDON_PATH'] = str(Path(script_path).parent)

    # create location name from dem filename
    name_parts = dem.stem.split('_')
    loc_name = '_'.join(name_parts[0:2])
    loc_path = grass_db / loc_name
    mapset_path = loc_path / 'PERMANENT'
    grs_dem = '_'.join(name_parts[0:2]) # Name for the GRASS raster created from the DEM

    # Create grass_db folder if it doesn't exist
    if not grass_db.exists():
        grass_db.mkdir(parents=True)
    os.environ['GISDBASE'] = str(grass_db)

    # Create location and mapset if it doesn't exist
    if not loc_path.exists():
        new_loc_cmd = '-c "{d}" -e "{l}"'.format(d=str(dem_path), l=str(loc_path))
        run_command_00(new_loc_cmd, "New Location: {}".format(loc_path), "ERROR: Location not created")

    # Run script
    geo_cmd = '{m}\  --exec python "{s}" dem="{d}"'.format(m=mapset_path, s=script_path, d=dem_path)
    run_command_00(geo_cmd, "Geomorphon tool run successfully", "ERROR: Issues running GRASS GIS script")

    #TODO: Print message when the script is done
    #TODO: Get output file paths and return them as a dict


def watershed_ext_00(dem_path, dem_resolution, grass_data_path, script_path,
                     grass_bin=None, min_basin_size=None):
    """Runs r.watershed on a single DEM and exports P and SRC files.

    Parameters
    ----------
    dem_path : str
        Path to the DEM to import
    dem_resolution : int or str
        Resolution of the DEM (20, 10, 5...)
    grass_data_path : str or Path obj
        Path to grass data root folder
    grass_bin : str or Path obj, optional
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

    if grass_bin == None:
        grass_bin = get_grass_bin_00()
    gbase = get_grass_dir_00(grass_bin)

    grass_db = Path(str(grass_data_path))
    dem = Path(str(dem_path))

    # =================================================================================================
    #TODO: Move this to its own function.

    # create location name from dem filename
    name_parts = dem.stem.split('_')
    loc_name = '_'.join(name_parts[0:2])
    loc_path = grass_db / loc_name
    mapset_path = loc_path / 'PERMANENT'
    grs_dem = '_'.join(name_parts[0:2]) # Name for the GRASS raster created from the DEM

    # Create grass_db folder if it doesn't exist
    if not grass_db.exists():
        grass_db.mkdir(parents=True)
    os.environ['GISDBASE'] = str(grass_db)

    # Create location and mapset if it doesn't exist
    if not loc_path.exists():
        new_loc_cmd = '-c "{d}" -e "{l}"'.format(d=str(dem_path), l=str(loc_path))
        run_command_00(new_loc_cmd, "New Location: {}".format(loc_path), "ERROR: Location not created")

    # =========================================================================================================

    # Pick minimum basin threshold if not specified:
    if min_basin_size is None:
        thresholds = {'20': 100, '10': 500, '5': 1200}
        if str(dem_resolution) in thresholds.keys():
            min_basin_size = int(thresholds[str(dem_resolution)])
        else:
            print("Minimum basin size required")

    # Run script
    os.environ['GRASS_ADDON_PATH'] = str(Path(script_path).parent) # TODO: Move to set_grass_envs

    watershed_cmd = '"{g}" {m}\  --exec python "{s}" dem="{d}" threshold={t} '.format(g=grass_bin, m=mapset_path, s=script_path, d=dem_path,
                                                                            t=min_basin_size)
    run_command_00(watershed_cmd, "Watershed tool run successfully", "ERROR: Issues running GRASS GIS script")


    #TODO: Print confirmation message when the script is done
    #TODO: Get output file paths and return them as a dict


if __name__ == "__main__":
    pass
    """
    db_path = r"D:\HSSD\Projects\Experimental\grassdata"        
    dem_path = r"D:\HSSD\Projects\Experimental\PilotBasins_20ft\LUMBR05\Surface\DSM01_DEM00\LUMBR05_DEM01_DEM00.tif"\
    
    gm_script_path = r"C:\HSSD\Code_Prjs\bharvey\grass_scripts\gr_geomorphon_00.py"
    geomorphons_ext_00(dem_path, db_path, gm_script_path)
    
    dem_res = 20
    w_script_path = r"C:\HSSD\Code_Prjs\bharvey\grass_scripts\gr_watershed_00.py"
    watershed_ext_00(dem_path, dem_res, db_path, w_script_path, min_basin_size=100)
    """
