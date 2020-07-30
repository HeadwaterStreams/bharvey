#!/usr/bin/env python3
#################################################################################
#
# MODULE:     gr_geomorphon_00
# AUTHOR(S):  bethany.harvey@ncdenr.gov
# PURPOSE:    Runs r.geomorphon and exports a file with valleys, hollows, and depressions
# DATE:       2020-07-06
#
#################################################################################

#%module
#% description: Runs r.geomorphon and exports GEOM file
#% keyword: raster
#% keyword: geomorphons
#% keyword: terrain patterns
#%end
#%option G_OPT_F_INPUT
#% key: dem
#% description: Absolute path to the DEM
#% required: yes
#%end
#%option
#% key: search
#% type: integer
#% required: yes
#% multiple: no
#% description: Outer search radius
#% answer: 30
#%end
#%option
#% key: skip
#% type: integer
#% required: yes
#% multiple: no
#% description: Inner search radius
#% answer: 0
#%end
#%option
#% key: flat
#% type: double
#% required: yes
#% multiple: no
#% description: Flatenss threshold (degrees)
#% answer: 1
#%end
#%option
#% key: dist
#% type: double
#% required: yes
#% multiple: no
#% description: Flatenss distance, zero for none
#% answer: 0
#%end


# TEST: Works from GRASS, test from `gr_external_00`

import sys

import grass.script as gscript


def geomorphon_00(dem_path, **kwargs):
    """

    Parameters
    ----------
    dem_path: str or Path obj
        Path to the original DEM
    kwargs: dict, optional
        All other arguments.
        search: Outer search radius. Use higher numbers for flatter areas. Default=3
        skip: Inner search radius. Default=0
        flat: Flatness threshold in degrees. Default=1
        dist: Default=0

    """

    from pathlib import Path

    import grass.script as gscript

    dem = Path(str(dem_path))
    name_parts = dem.stem.split('_')
    prj = name_parts[0]
    dem_ras = '_'.join(name_parts[0:2])
    dem_num = dem_ras[-2:]

    # Import the DEM and set region extent and projection to match it
    map_rasters = gscript.list_strings(type='raster')
    if dem_ras not in map_rasters:
        gscript.run_command('r.in.gdal', input=str(dem_path), output=dem_ras, verbose=True)
    gscript.run_command('g.region', raster=dem_ras, verbose=True)

    forms = '{p}_forms{n}'.format(p=prj, n=dem_num)
    gscript.run_command('r.geomorphon', elevation=str(dem_ras) + "@PERMANENT", forms=forms, **kwargs)

    # Reclassify. 10 -> 1:depression, 7 -> 2:hollow, 9 -> 3:valley
    g_ras = forms.replace('forms', 'geom')
    expr = "{o} = if({i}==10, 1, if({i}==7, 2, if({i}==9, 3, 0)))".format(o=g_ras, i=forms)
    gscript.raster.mapcalc(expr, overwrite=True)

    # Export the new file
    cls = dem.parent.parent.parent / "Surface_Flow"
    if cls.exists():
        grps = list(cls.glob('SFW*_DEM'+str(dem_num)))
    else:
        grps = []
    if len(grps) > 0:
        sfw = grps[0]
        sfw_num = sfw.name.split('_')[1][-2:]
    else:
        sfw = cls / 'SFW00_DEM'+str(dem_num)
        sfw_num = '00'
        sfw.mkdir(parents=True)

    out_file = sfw / "{p}_GEOM{g}_DEM{n}.tif".format(p=prj, g=sfw_num, n=dem_num)

    gscript.run_command('r.out.gdal', input=g_ras, output=str(out_file),
                        format="GTiff", type="Byte",
                        createopt="COMPRESS=DEFLATE,PREDICTOR=2")

    return out_file


def main():
    """Imports the DEM, runs r.geomorphon, and exports GEOM file

    Must be run from within the GRASS user interface.
    To run from outside GRASS, use `gr_external_00.geomorphon_ext_00`.
    """

    dem = options['dem']
    search = options['search']
    skip = options['skip']
    flat = options['flat']
    dist = options['dist']

    # Set values for optional params
    kwargs = {}
    if search:
        kwargs['search'] = search
    if skip:
        kwargs['skip'] = skip
    if flat:
        kwargs['flat'] = flat
    if dist:
        kwargs['dist'] = dist

    geomorphon_00(dem, **kwargs)

    return 0


if __name__ == "__main__":
    options, flags = gscript.parser()
    sys.exit(main())
