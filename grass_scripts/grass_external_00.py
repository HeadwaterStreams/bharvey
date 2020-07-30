#!/usr/bin/env python3
"""
Runs GRASS tools from outside the GRASS user interface.

Usage
-------
To run r.watershed, use `watershed_ext_00`.

To run r.geomorphon, use `geomorphon_ext_00`.

Other GRASS modules can be run using `run_grass_script_00`. This script sets any necessary variables and then sends commands to GRASS.
Any GRASS Python modules will be run using GRASS's Python installation.

The following parameters are the same for all functions where they exist:

Attributes
----------
dem_path : str
    Path to the DEM to import.
res : int
    Cell size of the DEM, in ft. Used as a suffix to separate locations based on DEMs with the same name but different resolutions.
    Also used to pick a sub-basin size threshold for the watershed tool.
grass_db : str
    Path to grass data root folder.
grass_bin : str, optional
    Path to grass7*.bat.

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
        osd / r'OSGeo4W64', # FIXME: Where is the grass7*.bat file located if installed via OSGeo?
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

    import shlex
    import subprocess
    import sys

    if grass_bin == None:
        grass_bin = get_grass_bin_00()

    cmd = '"{g}" {c}'.format(g=grass_bin, c=command)
    cmd = shlex.split(cmd)

    try:
        process = subprocess.Popen(cmd, shell=False,
                             stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True)
        out, err = process.communicate()
        # process = subprocess.check_output(cmd, stderr=subprocess.STDOUT, shell=False, text=True)

    except OSError as error:
        sys.exit("ERROR: Cannot find GRASS GIS start script"
                 " {cmd}: {error}".format(cmd=cmd[0], error=error))

    # if process.returncode != 0:
    #     sys.exit(" {cmd}: {error}".format(cmd=' '.join(cmd), error=err))
    # else:
    #     sys.exit(0)

    # TODO: return paths to any files that were created.


def run_grass_script_00(script_path, mapset_path, grass_bin=None, **kwargs):
    """Formats the command to run a python, bash, or batch script as a GRASS module.

    This function is called by `geomorphon_ext_00` and `watershed_ext_00`. It can be used directly to run other GRASS scripts.

    Parameters
    ----------
    script_path: str
        The python, bash, or batch script for GRASS to run.
    mapset_path: str
        Path to the GRASS mapset the script will be run in.
    grass_bin: str, optional
        Path to grass78.bat. Will search for it if not given.
    kwargs: dict, optional
        Any additional parameters to pass to the GRASS module.

    Returns
    -------
    # TODO: Get and return the paths of any new files that were created, for use in batch workflow scripts.
    """

    from pathlib import Path

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

    # Command string
    cmd = '"{m}" --exec {l} "{s}" {k}'.format(m=mapset_path, l=script_lang, s=script_path, k=kwarg_str)

    run_grass_command_00(cmd, grass_bin)

    #TODO: Return results


def location_00(dem_path, res, grass_db, grass_bin=None):
    """Creates a new GRASS location based on the source DEM filename.

    GRASS will create a mapset called 'PERMANENT' in the location automatically.

    # TODO: Add a suffix to differentiate locations based on files with different resolutions.
    # TODO: Add a step to create a new mapset within an existing location, to keep track of files for different runs?

    
    Parameters
    ----------
    dem_path: str or Path obj
    res: int or str
        Cell size of the DEM file, in feet.
    grass_db: str or Path obj
    grass_bin: str, optional

    Returns
    -------
    mapset_path: str
        Path to the GRASS mapset folder
    """

    import os
    from pathlib import Path
    
    # create location name from dem filename
    name_split = Path(str(dem_path)).stem.split('_')
    loc_name = '_'.join(name_split[0:2]) + "_" + str(res)
    loc_path = Path(str(grass_db)) / loc_name
    mapset_path = loc_path / 'PERMANENT'

    # If the grass_db folder doesn't exist, create it.
    grass_db = Path(str(grass_db))
    if not grass_db.exists():
        grass_db.mkdir(parents=True)
    os.environ['GISDBASE'] = str(grass_db)

    # If the location doesn't exist, create it. (GRASS will create a mapset called `PERMANENT` automatically.)
    if not loc_path.exists():
        new_loc_cmd = '-c "{d}" -e "{l}"'.format(d=str(dem_path), l=str(loc_path))
        run_grass_command_00(new_loc_cmd, grass_bin)

    return str(mapset_path)


def geomorphon_ext_00(dem_path, res, grass_db, script_path=None, search=None, skip=None, flat=None, dist=None,
                       grass_bin=None):
    """Runs geomorphon tool and exports a .tif file showing depressions, hollows, and valleys.

    Parameters
    ----------
    dem_path : str
        Path to the DEM to import.
    res : int or str
        Cell size of the DEM, in ft. Used to separate locations based on DEMs with the same name but different resolutions.
    grass_db : str
        Path to grass data root folder.
    script_path: str, optional
        Not needed if the script for GRASS to run is in the same folder as this file.
    grass_bin : str, optional
        Path to grass7*.bat.

    Returns
    -------
    # TODO: Return paths for use with batch scripts.

    """

    from pathlib import Path
    import os

    mapset_path = location_00(dem_path, res, grass_db)
    if script_path == None:
        script_path = Path(__file__).parent / 'gr_geomorphon_00.py'
    os.environ['GRASS_ADDON_PATH'] = str(Path(script_path).parent) # CHECK: Probably don't need this anymore.

    # Run script
    kwargs = dict(dem='"{}"'.format(dem_path))
    if search != None:
        kwargs['search'] = search
    if skip != None:
        kwargs['skip'] = skip
    if flat != None:
        kwargs['flat'] = flat
    if dist != None:
        kwargs['dist'] = dist

    run_grass_script_00(script_path, mapset_path, grass_bin, **kwargs)

    #TODO: Return result


def watershed_ext_00(dem_path, res, grass_db, script_path=None,
                     grass_bin=None, min_basin_size=None):
    """Runs r.watershed on a DEM and exports P and SRC files.

    Parameters
    ----------
    dem_path : str
        Path to the DEM to import
    res : int or str
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

    Returns
    -------
    # TODO: Return paths to new files for use with batch scripts.
    """
    
    from pathlib import Path
    import os

    if script_path == None:
        script_path = Path(__file__).parent / 'gr_watershed_00.py'

    os.environ['GRASS_ADDON_PATH'] = str(Path(script_path).parent)
    mapset_path = location_00(dem_path, res, grass_db)

    # Pick minimum basin threshold if not specified:
    if min_basin_size is None:
        thresholds = {'20': 160, '10': 600, '5': 2400} # TODO: Test these.
        if str(res) in thresholds.keys():
            min_basin_size = int(thresholds[str(res)])
        else:
            print("Minimum basin size required")

    # Script parameters
    kwargs = dict(dem='"{}"'.format(dem_path), threshold=int(min_basin_size))

    run_grass_script_00(script_path, mapset_path, grass_bin, **kwargs)

    #TODO: Return result


if __name__ == "__main__":
    pass

