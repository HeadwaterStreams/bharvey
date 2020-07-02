#!/usr/bin/env python3
"""
Runs GRASS watershed tool from outside the GRASS user interface.

You may need to edit paths, including the first line, which should be the path to the Python interpreter used by GRASS.


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


def watershed_ext_00(dem_path, dem_resolution, grass_data_path, script_path,
                     grass_bin=None, min_basin_size=None):
    """Runs r.watershed on a single DEM and exports P and SRC files.

    Because of problems with running grass modules from Python outside of the GRASS interface, this script sets all the necessary
    variables and then sends a command to the terminal to run GRASS with another module instead of directly working with GRASS.
    This way the two scripts can be run by separate Python installations.

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
    import sys
    import subprocess

    if grass_bin == None:
        grass_bin = get_grass_bin_00()
    gbase = get_grass_dir_00(grass_bin)

    grass_db = Path(str(grass_data_path))
    dem = Path(str(dem_path))

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
        new_loc_cmd = [grass_bin, '-c', dem_path, '-e', str(loc_path)]
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


    # Pick minimum basin threshold if not specified:
    if min_basin_size is None:
        thresholds = {'20': 100, '10': 500, '5': 1200}
        if str(dem_resolution) in thresholds.keys():
            min_basin_size = int(thresholds[str(dem_resolution)])
        else:
            print("Minimum basin size required")


    # Run script
    os.environ['GRASS_ADDON_PATH'] = str(Path(script_path).parent)

    cmd = '"{g}" {m}\  --exec python "{s}" dem="{d}" threshold={t} '.format(g=grass_bin, m=mapset_path, s=script_path, d=dem_path,
                                                                            t=min_basin_size)
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
    else:
        sys.exit("Watershed tool run succesfully.")

    #TODO: Print message when the script has run successfully
    #TODO: Get output file paths and return them as a dict


if __name__ == "__main__":
    pass

    """
    Test data:
    db_path = r"D:\HSSD\Projects\Experimental\grassdata"
    script_path = r"C:\HSSD\Code_Prjs\bharvey\grass_scripts\gr_watershed_00.py"

    dem_path = r"D:\HSSD\Projects\Experimental\PilotBasins_20ft\LUMBR05\Surface\DSM01_DEM00\LUMBR05_DEM01_DEM00.tif"
    resolution = 20
    min_basin = 100
    
    watershed_ext_00(dem_path, resolution, db_path, script_path)
    """

