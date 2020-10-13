#!/usr/bin/env python3
"""
Runs GRASS tools from outside the GRASS user interface.

Usage
-------
To run r.watershed, use `watershed_ext_00`.

To run r.geomorphon, use `geomorphon_ext_00`.

Other GRASS modules can be run using `run_grass_script_00`. This script sets variables and sends commands to GRASS.
Any GRASS Python modules will be run using GRASS's Python installation.

The following variables are the same for all functions where they exist:

`dem_path` is the path to the input DEM.
`res` is the size, in feet, of each cell in the DEM. It is used as a suffix to separate locations based on DEMs with
the same name but different resolutions. It's also used to pick a sub-basin size threshold for `watershed_ext_00`.
`grass_db` is the path to grass database root folder, where the locations are stored.
`grass_bin` is the path to grass7*.bat, which is used to run GRASS externally. The script will look for it in a few
typical directories, but you may need to supply the path.

"""


def get_grass_bin_00():
    """Looks for grass*.bat file on the computer.

    If there are multiple GRASS installations, returns the first one.
    """
    
    from pathlib import Path

    home = Path.home()
    osd = Path(home.anchor)

    # Directories to search for GRASS bat file
    search_dirs = [
        osd / r'Program Files\QGIS 3.10\bin',  #TODO: glob search so any QGIS version works
        osd / r'Program Files\GRASS78',  #TODO: glob search so any GRASS version works
        home / r'Apps\GRASS78',
        osd / r'OSGeo4W64',  #FIXME: Where is the grass7*.bat file located if installed via OSGeo?
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

    if grass_bin is None:
        grass_bin = get_grass_bin_00()

    cmd = '"{g}" {c}'.format(g=grass_bin, c=command)
    print("Starting GRASS: {}".format(cmd))
    cmd = shlex.split(cmd)

    try:
        process = subprocess.Popen(cmd, shell=False,
                                   stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True)
        out, err = process.communicate()

        print(out)
        print(err)

        return out, err

    except OSError as error:
        sys.exit("ERROR: Cannot find GRASS GIS start script. {cmd}: {error}".format(cmd=cmd[0], error=error))


def run_grass_script_00(script_path, mapset_path, grass_bin=None, **kwargs):
    """Formats the command to run a python, bash, or batch script as a GRASS module.

    Called by `geomorphon_ext_00` and `watershed_ext_00`. It can also be used directly to run other GRASS scripts.

    Parameters
    ----------
    script_path : str
        The python, bash, or batch script for GRASS to run.
    mapset_path : str
        Path to the GRASS mapset the script will be run in.
    grass_bin : str, optional
        Path to grass78.bat. Will search for it if not given.
    kwargs : dict, optional
        Any additional parameters to pass to the GRASS module.

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
    for k, v in kwargs.items():
        kwarg_str += '{}={} '.format(k, v)

    # Command string
    cmd = '"{m}" --exec {l} "{s}" {k}'.format(m=mapset_path, l=script_lang, s=script_path, k=kwarg_str)

    run_grass_command_00(cmd, grass_bin)


def location_00(dem_path, res, grass_db, grass_bin=None):
    """Creates a new GRASS location based on the source DEM filename.

    GRASS will create a mapset called 'PERMANENT' in the location automatically.

    Parameters
    ----------
    dem_path : str or Path obj
    res : int or str
        Cell size of the DEM file, in feet.
    grass_db : str or Path obj
    grass_bin : str, optional

    Returns
    -------
    mapset_path : str
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

    # If the location doesn't exist, create it.
    # GRASS will create a mapset called `PERMANENT` automatically.
    if not loc_path.exists():
        new_loc_cmd = '-c "{d}" -e "{l}"'.format(d=str(dem_path), l=str(loc_path))
        run_grass_command_00(new_loc_cmd, grass_bin)

    # TODO: Add a step to create a new mapset within an existing location?

    return str(mapset_path)


def new_file_path_00(dem_path, cls, grp_str, mod_str):
    """Creates new group and output file path from input file name.

    This is a workaround to check and return output file locations without passing output strings
    from the GRASS script to GRASS to command line output back to python.

    Parameters
    ----------
    dem_path : str
        Path to input DEM
    cls : str
        Name of class, example: "Surface_Flow"
    grp_str : str
        Group name, example: "SFW"
    mod_str : str
        Model file abbreviation, example: "P"

    Returns
    -------
    out_path : str
        Path to exported .tif file
    """

    from pathlib import Path

    dem = Path(str(dem_path))
    dsm = dem.parent
    old_grp = dsm.name.split('_')[0]
    prj = dsm.parent.parent
    cls = prj / cls

    grps = list(cls.glob(grp_str + '*'))

    # Find the highest group number
    if len(grps) > 0:
        grpnos = []
        for grp in grps:
            grpno = grp.name.split("_")[0][-2:]
            grpnos.append(int(grpno))
        new_grp_no = ('0' + str(max(grpnos) + 1))[-2:]
    else:
        new_grp_no = '00'

    new_grp = cls / "{}{}_{}".format(grp_str, new_grp_no, old_grp)

    # New file path to create
    out_file_name = "{}_{}{}_{}.tif".format(prj.name, mod_str, new_grp_no,
                                            dem.name.split("_")[1])
    out_path = new_grp / out_file_name

    return str(out_path)


def geomorphon_ext_00(dem_path, res, grass_db, script_path=None, search=None, skip=None, flat=None, dist=None,
                      grass_bin=None):  # FIXME
    """Runs geomorphon tool and exports a .tif file.

    The GEOM file is saved in the first SFW group with the input DSM group as its source.
    The exported file includes depressions (1), hollows (2), and valleys (3). All other landforms
    have a cell value of 0.

    Parameters
    ----------
    dem_path : str
        Path to the DEM to import.
    res : int or str
        Cell size of the DEM, in ft. Used to separate locations based on DEMs with the same name but different resolutions.
    grass_db : str
        Path to grass data root folder.
    script_path: str, optional
        Not needed if the script for GRASS to run is in the same folder as this script. #TEST
    search : int
        Outer search radius. Use higher numbers for flatter areas. Default=3
    skip : int
        Inner search radius. Default=0
    flat : int
        Flatness threshold in degrees. Default=1
    dist : int
        Default=0
    grass_bin : str, optional
        Path to grass7*.bat.

    Returns
    -------
    out_path : str
        Path to exported file.

    """

    from pathlib import Path
    import os

    mapset_path = location_00(dem_path, res, grass_db)
    if script_path is None:
        script_path = Path(__file__).parent / 'gr_geomorphon_00.py'
        print(script_path) #TEST PRINT
    os.environ['GRASS_ADDON_PATH'] = str(Path(script_path).parent)  #CHECK: Probably don't need this anymore.

    # Get new file path to check for after running script
    dem = Path(dem_path)
    dsm = dem.parent
    prj = dsm.parent.parent
    cls = prj / "Surface_Flow"
    grps = list(cls.glob("SFW*_" + dsm.name.split('_')[0]))
    if len(grps) > 0:
        grp = grps[0]
        out_path = grp / "{}_GEOM{}_{}".format(prj.name, grp.name.split('_')[0][-2:], dem.stem.split('_')[0])
    else:
        out_path = new_file_path_00(dem_path, "Surface_Flow", "SFW", "GEOM")

    # Run script
    kwargs = dict(dem='"{}"'.format(dem_path))
    if search is not None:
        kwargs['search'] = search
    if skip is not None:
        kwargs['skip'] = skip
    if flat is not None:
        kwargs['flat'] = flat
    if dist is not None:
        kwargs['dist'] = dist

    run_grass_script_00(script_path, mapset_path, grass_bin, **kwargs)

    # Check for new file
    if out_path.exists():
        print("Geomorphon raster exported to {}.".format(out_path))
        return str(out_path)
    else:
        print("Error: {} was not created.".format(out_path))
        return "error"


def watershed_ext_00(dem_path, res, grass_db, script_path=None,
                     grass_bin=None, min_basin_size=None):
    """Runs r.watershed on a DEM and exports P and SRC files.

    Parameters
    ----------
    dem_path : str
        Path to the DEM to import.
    res : int or str
        Resolution of the DEM (20, 10, 5...)
    grass_db : str or Path obj
        Path to grass data root folder.
    script_path: str or Path obj, optional
        Not needed if the script for GRASS to run is in the same folder as this file. #TEST
    grass_bin : str or Path obj, optional
        Path to grass7*.bat.
    min_basin_size : int or str, optional
        Minimum size, in cells, for a sub-basin.
        If not supplied, a default value will be selected based on `res`.

            =====  ==============
            res    min_basin_size
            =====  ==============
            20 ft  400 cells
            10 ft  1600 cells
            5  ft  6400 cells
            =====  ==============

    Returns
    -------
    out_paths : dict
        Paths to exported .tif files.
    """
    
    from pathlib import Path
    import os

    if script_path is None:
        script_path = Path(__file__).parent / 'gr_watershed_00.py'
        print(script_path) #TEST PRINT

    os.environ['GRASS_ADDON_PATH'] = str(Path(script_path).parent)
    mapset_path = location_00(dem_path, res, grass_db)

    # Pick minimum basin threshold if not specified
    if min_basin_size is None:
        thresholds = {'20': 400, '10': 1600, '5': 6400}  #TODO: Needs more testing for 10 and 5 ft resolution
        if str(res) in thresholds.keys():
            min_basin_size = int(thresholds[str(res)])
        else:
            print("Minimum basin size required")

    # File paths to be created (Workaround instead of passing output strings from GRASS script to command to python)
    p = new_file_path_00(dem_path, 'Surface_Flow', 'SFW', 'P')
    src = new_file_path_00(dem_path, 'Stream_Pres', 'STPRES', 'SRC')

    # Script parameters
    kwargs = dict(dem='"{}"'.format(dem_path), threshold=int(min_basin_size))

    run_grass_script_00(script_path, mapset_path, grass_bin, **kwargs)

    # Check if new files were created
    out_paths = {}
    if Path(p).exists():
        out_paths.update({'p': p})
        print("Flow direction exported to {}.".format(p))
        if Path(src).exists():
            out_paths.update({'src': src})
            print("Stream segments exported to {}.".format(src))
        else:
            print("Error: {} was not created.".format(src))
        return out_paths
    else:
        print("Error: {} was not created.".format(p))
        return "error"


if __name__ == "__main__":
    pass
