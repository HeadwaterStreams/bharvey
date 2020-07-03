#!/usr/bin/env python3
#################################################################################
#
# MODULE:     gr_geomorphon_00
# AUTHOR(S):  bharvey2
# PURPOSE:    Runs geomorphons tool and converts the resulting files to use with TauDEM
# DATE:       2020-07-02
#
#################################################################################

#%module
#% description: Runs r.geomorphon and exports GEOM files
#% keyword: raster
#% keyword: terrain patterns
#%end
#%option G_OPT_F_INPUT
#% key: dem
#% description: Absolute path to the DEM
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


def geomorphon_00(in_raster, dem, search=3, skip=0, flat=1, dist=0):
    """Run r.geomorphon

    Parameters
    ----------
    in_raster : str
        Name of imported dem file
    dem: str or Path obj
        original DEM used
    search: int
        Outer search radius. Default=3
    skip: int
        Inner search radius. Default=0
    flat: float
        Flatness threshold in degrees. Default=1
    dist: float
        Default=0

    Returns
    -------
    dict
    """

    prj = in_raster.split('_')[0]
    num = in_raster[-2:]

    out_raster = '{}_GEOM{}'.format(prj, num)

    gscript.core.run_command('r.geomorphon', elevation=str(in_raster)+"@PERMANENT", forms=out_raster, search=search, skip=skip, flat=flat, dist=dist, overwrite=True)

    g_ras = out_raster.replace("forms", "g")


    # TODO: Any reclassification or conversion needed for geomorphons file




    g_path = export_raster_00(g_ras, 'Surface_Flow', 'SFW', 'GEOM', str(dem))
    return g_path


def export_raster_00(in_raster, class_name, group_str, name, dem_path):
    """Export GRASS rasters to .tif files

    Parameters
    ----------
    in_raster : str
        Name of GRASS raster to export
    class_name : str
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

    class_path = prj / class_name

    grps = list(class_path.glob(group_str + '*'))

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
    new_group = class_path / "{}{}_{}".format(group_str, new_group_no, old_group)

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

def dem_to_geom_00(dem_path, search=3, skip=0, flat=1, dist=0):  #TODO
    """Run import, geomorph, mapcalc, and export tools

    Parameters
    ----------
    dem_path : str or object
        Path to DEM file

    Returns
    -------
    output_paths : dict
        Paths to exported files
    """

    # Import dem
    elev_raster = import_dem_00(str(dem_path))

    # Run r.geomorphon
    g = geomorphon_00(str(elev_raster), dem_path, search, skip, flat, dist)

    return {'geom': g}


def main():
    """Imports the DEM, runs r.geomorphon, and exports GEOM file

    Must be run from within the GRASS user interface.
    To run from outside GRASS, use `gr_external_00.geomorphon_ext_00`.
    """

    options, flags = gscript.parser()
    dem_path = options['dem']

    dem_to_geom_00(dem_path)

    return 0


if __name__ == "__main__":
    sys.exit(main())
