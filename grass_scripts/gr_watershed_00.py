#!/usr/bin/env python3
#################################################################################
#
# MODULE:     gr_watershed_00
# AUTHOR(S):  bharvey2
# PURPOSE:    Run r.watershed and convert the resulting files to use with TauDEM
# DATE:       2020-04-27
#
#################################################################################

#%module
#% description: Runs r.watershed and exports SRC and P files
#% keyword: raster
#% keyword: hydrology
#% keyword: watershed
#%end
#%option G_OPT_F_INPUT
#% key: dem
#% description: Absolute path to the DEM
#% required: yes
#%end
#%option
#% key: threshold
#% type: integer
#% label: Minimum size of exterior watershed basins, in cells.
#% description: Depends on resolution. Ex: 20ft: 100, 10ft: 500, 5ft: 1200
#% multiple: no
#% required: yes
#%end

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
    dem_ras : str
        Name of the imported raster
    """

    name_parts = Path(str(dem_path)).name.split('_')
    dem_ras = '_'.join(name_parts[0:2])

    gscript.run_command('r.in.gdal', input=str(dem_path), output=dem_ras, overwrite=True, verbose=True)  #TODO: Instead of overwrite, check if it has already been imported.

    gscript.run_command('g.region', raster=dem_ras, verbose=True)

    return dem_ras


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


def drain_to_p_00(drain, dem):
    """Convert a drainage direction raster to P file

    Parameters
    ----------
    drain : str
        Name of GRASS drainage direction raster
    dem : str
    """

    p_ras = drain.replace("drain", "p")

    expr = "{o} = if( {i}>=1, if({i}==8, 1, {i}+1), null() )".format(
        o=p_ras, i=drain)

    gscript.raster.mapcalc(expr, overwrite=True)

    p_path = export_raster_00(p_ras, 'Surface_Flow', 'SFW', 'P', str(dem))

    return p_path


def stream_to_src_00(stream, dem):
    """Convert a stream segments raster to SRC file

    Parameters
    ----------
    dem : str or obj
        Path to DEM file
    stream : str
        Name of GRASS stream raster
    """

    src_ras = stream.replace('stream', 'src')

    # All non-zero values to 1
    expr = "{o} = if(isnull({i}), 0, 1)".format(o=src_ras, i=stream)
    gscript.raster.mapcalc(expr, overwrite=True)

    src_path = export_raster_00(src_ras, 'Stream_Pres', 'STPRES', 'SRC', dem)

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

    grps = list(group_parent_path.glob(group_str + '*'))

    # Find the highest group number
    if len(grps) > 0:
        grpnos = []
        for grp in grps:
            grpno = grp.name.split("_")[0][-2:]
            grpnos.append(int(grpno))
        new_group_no = ('0' + str(max(grpnos) + 1))[-2:]
    else:
        new_group_no = '00'
    old_group = dsm.name.split('_')[0]
    new_group = group_parent_path / "{}{}_{}".format(group_str, new_group_no, old_group)

    new_group.mkdir(parents=True)

    # Export file path
    out_file_name = "{}_{}{}_{}.tif".format(huc, name, new_group_no,
                                            dem.name.split("_")[1])
    out_path = new_group / out_file_name

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
    output_paths : dict
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

    return {'src': src, 'p': p}


def main():
    """Imports the DEM, runs r.watershed, and exports SRC and P files

    Must be run from within the GRASS user interface.
    To run from outside GRASS, use watershed_ext_00() or watershed_batch_00().
    """

    options, flags = gscript.parser()
    dem_path = options['dem']
    threshold = options['threshold']

    dem_to_src_00(dem_path, threshold)

    return 0


if __name__ == "__main__":
    sys.exit(main())
