#!/usr/bin/env python3
"""
Runs GRASS tools from outside the GRASS user interface.

This script sets the necessary variables and then sends commands to GRASS via the command line.
Any GRASS modules will be run using GRASS's Python installation.

The script will look for the GRASS binary file (grass7*.bat) on your computer, but if you installed GRASS via OSGeo,
or if is not in one of the usual directories, you may need to supply the path.

"""


def get_grass_bin_00():
    """Looks for grass7*.bat file on the computer."""
    
    from pathlib import Path

    home = Path.home()
    osd = Path(home.anchor)

    # Locations to search for GRASS bat file
    search_dirs = [
        osd / r'Program Files\QGIS 3.10\bin',
        osd / r'Program Files\GRASS78',
        home / r'Apps\GRASS78',
        osd / r'OSGeo4W64',
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
    #     searchdirs.extend([p for p in list(sd.rglob("*")) if (p.is_dir() and 'grass' in p.name.lower())])

    grass_paths = []
    for d in search_dirs:
        if d.exists():
            grass_paths = list(Path(d).glob('**/grass*.bat'))
            if len(grass_paths) >= 1:
                break

    gb = grass_paths[0]
    return str(gb)


def run_grass_command_00(command, grass_bin=None):
    """Runs GRASS from the command line, using the provided parameters.

    Parameters
    ----------
    command: str
        Command to run.
    grass_bin: str or Path obj, optional
        Path to grass78.bat

    Returns
    -------
    output: dict
        Command output and files created, if any.

    """

    import shlex
    import subprocess
    import sys

    if grass_bin == None:
        grass_bin = get_grass_bin_00()

    cmd = '"{g}" {c}'.format(g=grass_bin, c=command)
    cmd = shlex.split(cmd)

    try:
        p = subprocess.Popen(cmd, shell=False,
                             stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True)
        out, err = p.communicate()
        p = subprocess.check_output(cmd, stderr=subprocess.STDOUT, shell=False, text=True)

    except OSError as error:
        sys.exit("ERROR: Cannot find GRASS GIS start script"
                 " {cmd}: {error}".format(cmd=cmd[0], error=error))

    if p.returncode != 0:
        sys.exit(" {cmd}: {error}".format(cmd=' '.join(cmd), error=err))
    else:
        sys.exit("Done")



def run_grass_script_00(script_path, mapset_path, grass_bin=None, **kwargs):
    """Runs a python, bash, or batch script as a GRASS module

    Parameters
    ----------
    script_path: str or Path obj
        Path to the script for GRASS to run.
    mapset_path: str or Path obj
        Path to the GRASS mapset the script will be run in.
    grass_bin: str, optional
        Path to grass78.bat. Will search for it if not given.
    kwargs: dict, optional
        Any parameters for the script.


    """

    from pathlib import Path
    import shlex
    import subprocess
    import sys

    if grass_bin == None:
        grass_bin = get_grass_bin_00()

    script = Path(str(script_path))
    if script.suffix == 'py':
        script_lang = 'python'
    elif script.suffix == 'sh':
        script_lang = 'sh'
    else:
        script_lang = ''

    kwarg_str = ''
    for k,v in kwargs.items():
        kwarg_str += '{}={} '.format(k,v)

    # Create command string

    cmd = '"{b}" "{m}" --exec {l} "{s}" {k}'.format(b=grass_bin, m=mapset_path, l=script_lang, s=script_path, k=kwarg_str)
    print("Command: {}".format(cmd))

    # Run the script and collect any output messages.
    try:
        p = subprocess.Popen(shlex.split(cmd), shell=False,
                             stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True)
        out, err = p.communicate()

    except OSError as error:
        sys.exit("ERROR: Cannot find GRASS GIS start script"
                 " {c}: {e}".format(c=cmd[0], e=error))

    if p.returncode != 0:
        sys.exit("{c}: {e}".format(c=' '.join(cmd), e=err))
    else:
        sys.exit("done")


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
    
    grass_interpreter = os.path.join(gisbase, "Python37", "python.exe")
    os.environ['GRASS_PYTHON'] = grass_interpreter
    
    sys.path.append(gisbase)
    sys.path.append(grass_py)
    sys.path.append(grass_interpreter)


    return grass_interpreter


def location_00(dem_path, grass_db):
    """Creates a new GRASS location if it doesn't exist.
    
    Parameters
    ----------
    dem_path: str or Path obj
    
    grass_db: str or Path obj
    """
    import os
    from pathlib import Path
    
    # create location name from dem filename
    name_split = Path(str(dem_path)).stem.split('_')
    loc_name = '_'.join(name_split[0:2])
    loc_path = Path(str(grass_db)) / loc_name
    mapset_path = loc_path / 'PERMANENT'

    # Create grass_db folder if it doesn't exist
    grass_db = Path(str(grass_db))
    if not grass_db.exists():
        grass_db.mkdir(parents=True)
    os.environ['GISDBASE'] = str(grass_db)

    # Create location and mapset if it doesn't exist
    if not loc_path.exists():
        new_loc_cmd = '-c "{d}" -e "{l}"'.format(d=str(dem_path), l=str(loc_path))
        run_grass_command_00(new_loc_cmd)
        
    return mapset_path


def geomorphon_ext_00(dem_path, grass_db, script_path=None, search=None, skip=None, flat=None, dist=None,
                       grass_bin=None):
    """Runs geomorphon tools on a single DEM.


    Parameters
    ----------
    dem_path : str
        Path to the DEM to import
    grass_db : str or Path obj
        Path to grass data root folder
    script_path: str or Path obj, optional
        Not needed if the script for GRASS to run is in the same folder as this file.
    grass_bin : str or Path obj, optional
        Path to grass7*.bat

    """
    from pathlib import Path
    import os

    mapset_path = location_00(dem_path, grass_db)
    if script_path == None:
        script_path = Path(__file__).parent / 'gr_geomorphon_00.py'
    os.environ['GRASS_ADDON_PATH'] = str(Path(script_path).parent)

    # Run script
    #geo_cmd = '{m}\  --exec python "{s}" dem="{d}"'.format(m=mapset_path, s=script_path, d=dem_path)
    kwargs = dict(dem='"{}"'.format(dem_path))
    if search != None:
        kwargs['search'] = search
    if skip != None:
        kwargs['skip'] = skip
    if flat != None:
        kwargs['flat'] = flat
    if dist != None:
        kwargs['dist'] = dist

    run_grass_script_00(script_path, mapset_path, **kwargs)

    dem = Path(str(dem_path))
    prj = dem.stem.split('_')[0]
    cls = dem.parent.parent.parent / "Surface_Flow"
    model = dem.stem.split('_')[1]
    geom_files = list(cls.rglob(prj + '_GEOM*_' + model + ".tif"))
    if len(geom_files) > 0:
        outfile = geom_files[0]
        print(str(outfile))
        return dict(geom=str(outfile))
    else:
       print("Error")


def watershed_ext_00(dem_path, dem_resolution, grass_db, script_path=None,
                     grass_bin=None, min_basin_size=None):
    """Runs r.watershed on a single DEM and exports flow direction as a P file.

    Parameters
    ----------
    dem_path : str
        Path to the DEM to import
    dem_resolution : int or str
        Resolution of the DEM (20, 10, 5...)
    grass_db : str or Path obj
        Path to grass data root folder
    script_path: str or Path obj, optional
        Not needed if the script for GRASS to run is in the same folder as this file.
    grass_bin : str or Path obj, optional
        Path to grass7*.bat
    min_basin_size : int or str, optional
        Minimum size, in cells, for a sub-basin.
        Leave blank to select automatically based on `res`.
    """
    
    from pathlib import Path
    import os

    if script_path == None:
        script_path = Path(__file__).parent / 'gr_watershed_00.py'
    os.environ['GRASS_ADDON_PATH'] = str(Path(script_path).parent)
    mapset_path = location_00(dem_path, grass_db)

    # Pick minimum basin threshold if not specified:
    if min_basin_size is None:
        thresholds = {'20': 160, '10': 600, '5': 2400}
        if str(dem_resolution) in thresholds.keys():
            min_basin_size = int(thresholds[str(dem_resolution)])
        else:
            print("Minimum basin size required")

    # Script parameters
    kwargs = dict(dem='"{}"'.format(dem_path), threshold=int(min_basin_size))

    run_grass_script_00(script_path, mapset_path, **kwargs)

    # watershed_cmd = '"{m}"  --exec python "{s}" dem="{d}" threshold={t} '.format(g=grass_bin, m=mapset_path, s=script_path, d=dem_path,
    #                                                                         t=min_basin_size)
    # run_grass_command_00(watershed_cmd)



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
