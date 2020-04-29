#!/usr/bin/env python3
"""
Runs GRASS scripts from outside the GRASS interface.




"""


def watershed_ext_00(dem_path, resolution, grass_db,
                     grass_bin, min_basin_size=None):
    """Runs r.watershed on a single DEM and exports P and SRC files.

    Parameters
    ----------
    dem_path : str or object
        Path to the DEM to import
    resolution : int
        Resolution of the DEM (20, 10, 5...)
    grass_db : str or object
        Path to grass data root folder
    grass_bin : str or Path obj
        Path to grass installation directory.
    min_basin_size : int
        Minimum size, in cells, for a subbasin
        Depends on resolution. Leave blank to select automatically.

    Returns
    -------
    out_files : dict
        Paths to exported files

    #TODO: Move the setup into a separate function

    """
    from pathlib import Path
    import os
    import sys
    import subprocess

    # Get grass_base and python path
    # query GRASS GIS itself for its GISBASE
    basecmd = [grass_bin, '--config', 'path']
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

    # set GISBASE environment variable
    os.environ['GISBASE'] = grass_base

    # define GRASS-Python environment
    grass_py = os.path.join(grass_base, "etc", "python")
    sys.path.append(grass_py)


    # Get location name
    name_parts = Path(str(dem_path)).name.split('_')
    location_name = '_'.join(name_parts[0:2])

    # Create location if it doesn't exist
    if not os.path.exists(grass_db):
        os.mkdir(grass_db)
    grass_location_path = os.path.join(grass_db, location_name)
    if not os.path.exists(grass_location_path):
        startcmd = [grass_bin, '-c', dem_path, '-e', grass_location_path]
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

    import grass.script as gscript
    import grass.script.setup as gsetup
    import gr_watershed_00 as grw

    rc_file = gsetup.init(grass_base, grass_db, location_name)

    # Run r.watershed

    if min_basin_size is None:
        thresholds = {'20': 100, '10': 500, '5': 1200}

        if str(resolution) in thresholds.keys():
            min_basin_size = thresholds[str(resolution)]
        else:
            print("Minimum basin size required")


    out_files = grw.dem_to_src_00(dem_path, min_basin_size) #FIXME

    return out_files


def main():
    pass


if __name__ == "__main__":
    main()

