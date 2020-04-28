#!/usr/bin/env python3
#################################################################################
#
# MODULE:     gr_streams
# AUTHOR(S):  bharvey2
# PURPOSE:    Run r.watershed and convert the resulting files to use with TauDEM
# DATE:       2020-04-21
#
# NOTE: This script has no setup functions and must be run from within GRASS.
# From GRASS GUI, click File > Launch script.
#
#################################################################################

# %module
# % description: Runs r.watershed and exports SRC and P files
# % keyword: raster
# % keyword: hydrology
# % keyword: watershed
# % keyword: export
# %end
# %option G_OPT_F_INPUT
# % key: dem_path
# % description: Absolute path to the DEM
# %end
# %option
# % key: threshold
# % type: integer
# % label: Minimum size of exterior watershed basins, in cells.
# % description: Depends on resolution. Ex: 20ft: 100, 10ft: 500, 5ft: 1200
# % multiple: no
# % required: yes
# %end

import sys
from pathlib import Path

import grass.script as gscript


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

    # Import the DEM
    gscript.run_command('r.in.gdal', input=str(dem_path),
                        output=out_raster, overwrite=True)

    # Set computational region
    gscript.run_command('g.region', raster=out_raster)

    return out_raster


def get_threshold_00(resolution):
    """Minimum basin size, based on resolution.

    Provides a reasonable minimum basin size for the resolution of the file.
    It will be more appropriate for some regions than others.

    ..note::
        This does NOT work when the module is run from within GRASS.

    Parameters
    ----------
    resolution : int
        Resolution of the input DEM

    Returns
    -------
    threshold : int
        Value for minimum basin size, based on resolution
    """

    thresholds = {'20': 100, '10': 500, '5': 1200}

    if str(resolution) in thresholds.keys():
        threshold = thresholds[str(resolution)]
        return threshold
    else:
        return "Minimum basin size required"


def watershed_00(in_raster_name, threshold):
    """Run r.watershed

    Parameters
    ----------
    in_raster_name : str
        Name of imported dem file
    threshold : int
        Minimum size, in map cells, of individual watersheds. If
        not specified, choose based on resolution.

    Returns
    -------
    watershed_rasters : dict
    """

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

    gscript.core.run_command('r.watershed', threshold=threshold, overwrite=True,
                             **watershed_rasters)

    return watershed_rasters


def drain_to_p_00(in_raster, dem):
    """Convert a drainage direction raster to P file

    Parameters
    ----------
    in_raster : str
        Name of GRASS drainage direction raster
    dem : str
    """

    out_raster = in_raster.replace("drain", "p")

    expr = "{o} = if( {i}>=1, if({i}==8, 1, {i}+1), null() )".format(
        o=out_raster, i=in_raster)

    gscript.raster.mapcalc(expr, overwrite=True)

    p_path = export_raster_00(out_raster, 'Surface_Flow', 'SFW', 'P', str(dem))

    return p_path


def stream_to_src_00(in_raster, dem):
    """Convert a stream segments raster to SRC file

    Parameters
    ----------
    dem : str or obj
        Path to DEM file
    in_raster : str
        Name of GRASS stream raster
    """

    out_raster = in_raster.replace('stream', 'src')

    # All non-zero values to 1
    expr = "{o} = if(isnull({i}), 0, 1)".format(o=out_raster, i=in_raster)
    gscript.raster.mapcalc(expr, overwrite=True)

    src_path = export_raster_00(out_raster, 'Stream_Pres', 'STPRES', 'SRC', dem)

    return src_path


def export_raster_00(in_raster, group_parent_name, group_str, name, dem_path):
    """Export GRASS rasters to .tif files

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

    dem = Path(str(dem_path))
    dsm = dem.parent
    prj = dsm.parent.parent

    huc = dem.stem.split('_')[0]

    group_parent_path = prj / group_parent_name

    grps = group_parent_path.glob(group_str + '*')

    if grps:
        grpnos = []
        for grp in grps:
            grpno = grp.name.split("_")[0][-2:]
            grpnos.append(int(grpno))
        new_group_no = ('0' + str(max(grpnos) + 1))[-2:]
    else:
        new_group_no = '00'
    old_group = dsm.name.split('_')[0]
    new_group = group_parent_path / "{}{}_{}".format(group_str, new_group_no, old_group)
    Path.mkdir(new_group)

    # Export file path
    out_file_name = "{}_{}{}_{}.tif".format(huc, name, new_group_no,
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

def dem_to_src_00(dem_path, threshold):
    """Run import, watershed, mapcalc, and export tools

    Parameters
    ----------
    dem_path : str or object
        Path to DEM file
    threshold : int
        Minimum size of watershed basin.

    Returns
    -------
    output_paths : list
        Paths to exported files
    """

    # Import dem
    elev_raster = import_dem_00(str(dem_path))

    # Run r.watershed
    watershed_rasters = watershed_00(str(elev_raster), threshold)
    stream = watershed_rasters['stream']
    drain = watershed_rasters['drainage']

    # Reclassify and export GRASS rasters for use with TauDEM
    src = stream_to_src_00(stream, dem_path)

    p = drain_to_p_00(drain, dem_path)

    return {dem_path: {'src': src, 'p': p}}


def main():
    """Imports the DEM, runs r.watershed, and exports SRC and P files

    Must be run from within the GRASS user interface.
    To run from outside GRASS, use watershed_ext_00() or watershed_batch_00().
    """

    options, flags = gscript.parser()
    dem_path = options['dem_path']
    threshold = options['threshold']

    dem_to_src_00(dem_path, threshold)

    return 0


if __name__ == "__main__":
    sys.exit(main())
