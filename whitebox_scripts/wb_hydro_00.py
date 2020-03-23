#! python3
"""
Updated: 2020-03-20

From initial DEM and extracted pipe files, create 3 new DSM groups:
- DEM with culverts
- DEM with breached depressions
- DEM with culverts and breached depressions

Quick & easy usage: to create all DSM groups, use:
process_dems_00([list of paths to pipe files], dem_path)
at line 271
"""


def new_group_00(source_path):
    """ Create the next group in the input file's class
    Parameters
    ----------
    source_path : str
        Path to source file
    """

    import os
    import re

    in_file_name = os.path.basename(source_path)
    source_str = in_file_name.split("_")[1]
    source_str = source_str[:-2]

    in_grp_path = os.path.dirname(source_path)
    in_grp_parent = os.path.dirname(in_grp_path)

    grpRegex = re.compile(r'(\w{2,8})(\d{2})_(\w{2,9})$')
    mo = grpRegex.search(re.escape(in_grp_path))
    grp_name = mo.group(1)
    in_grpno = mo.group(2)

    grps = os.listdir(in_grp_parent)

    grpnos = []
    for g in grps:
        new_mo = grpRegex.search(g)
        grpno = new_mo.group(2)
        grpnos.append(int(grpno))

    out_grpno = ('0' + str(max(grpnos) + 1))[-2:]
    out_grp = "{}{}_{}{}".format(grp_name, out_grpno, source_str, in_grpno)
    out_grp_path = os.path.join(in_grp_parent, out_grp)
    os.mkdir(out_grp_path)

    return out_grp_path


def new_file_00(in_file_path, name, out_ext, out_grp_path=None):
    """
    Parameters
    ----------
    in_file_path: string
        Path to input file
    name: string
        Example: "DEM"
    out_ext: string
        File extension for the output file. Example: "shp"
    out_grp_path: string
        Path to output directory. If none given, uses input directory.
    """

    import os
    import re

    in_file_name = os.path.basename(in_file_path)
    in_grp_path = os.path.dirname(in_file_path)

    fileRegex = re.compile(r'(\w{2,9}\d{2})_(\w{2,9})(\d{2})_\w{2,12}_?\w*\.\w{1,5}')
    mo = fileRegex.search(in_file_name)
    huc = mo.group(1)
    source_name = mo.group(2)
    in_grpno = mo.group(3)

    if out_grp_path is not None:
        grpnoRegex = re.compile(r'(\w{2,9})(\d{2})_\w{2,9}$')
        grp_mo = grpnoRegex.search(out_grp_path)
        out_grpno = grp_mo.group(2)
    else:
        out_grp_path = in_grp_path
        out_grpno = in_grpno

    out_file_name = "{}_{}{}_{}{}.{}".format(huc, name, out_grpno, source_name, in_grpno, out_ext)
    out_file_path = os.path.join(out_grp_path, out_file_name)

    return out_file_path


def check_exists_00(file_path):
    """Check whether the file was actually created.
    Parameters
    ----------
    file_path : str
        Path to file that should have been created
    """

    from pathlib import Path

    file = Path(file_path)
    if file.exists():
        return True
    else:
        return False


def merge_pipes_00(in_pipe_paths):
    """ Merge culvert features from multiple files, save to a new Hydro_Route group
    Parameters
    ----------
    in_pipe_paths : list
        List of pipe files to merge. Pipe files should already be clipped to basin extent.
    Returns
    -------
        Path to merged pipe file, in new Hydro_Route group
    """

    from WBT.whitebox_tools import WhiteboxTools
    wbt = WhiteboxTools()

    out_group = new_group_00(in_pipe_paths[-1])
    output_path = new_file_00(in_pipe_paths[-1], "PIPES", "shp", out_group)

    wbt.merge_vectors(';'.join(in_pipe_paths), output_path)

    if check_exists_00(output_path):
        return output_path
    else:
        return False


def extend_pipes_00(in_pipe_path, dist='20.0'):
    """ Extend individual culvert lines at each end, by the specified distance.
    Parameters
    ----------
    in_pipe_path : str
        Path to pipe file
    dist : str
        Distance to extend each line in both directions
    """

    from WBT.whitebox_tools import WhiteboxTools
    wbt = WhiteboxTools()

    output_path = new_file_00(in_pipe_path, "XTPIPE", "shp")
    wbt.extend_vector_lines(in_pipe_path, output_path, dist)

    if check_exists_00(output_path):
        return output_path
    else:
        return False


def pipes_to_raster_00(in_pipe_path, in_dem_path):
    """ Convert the pipes feature to a raster. Lines will be 1 cell wide.
    Parameters
    ----------
    in_pipe_path : str
        Path to the pipe file to buffer
    in_dem_path : str
        Path to the base DEM
    Returns
    -------
    output_path : str
        Path to the new raster file
    """

    from WBT.whitebox_tools import WhiteboxTools
    wbt = WhiteboxTools()

    # Create pipe raster file
    output_path = new_file_00(in_pipe_path, "PIPR", "tif")
    wbt.vector_lines_to_raster(in_pipe_path, output_path, field="FID", nodata=True,
                               base=in_dem_path)

    if check_exists_00(output_path):
        return output_path
    else:
        return False


def zone_min_00(in_dem_path, in_zones_path):
    """Sets the value of cells covered by culvert zones to the minimum elevation within each zone.
    Parameters
    ----------
    in_dem_path : str
        Path to input DEM file
    in_zones_path : str
        Path to culvert raster file
    """

    from WBT.whitebox_tools import WhiteboxTools
    wbt = WhiteboxTools()

    output_path = new_file_00(in_zones_path, "MIN", "tif")
    wbt.zonal_statistics(in_dem_path, in_zones_path, output_path, stat="minimum", out_table=None)

    if check_exists_00(output_path):
        return output_path
    else:
        return False


def burn_min_00(in_dem_path, in_zones_path):
    """Creates a new DSM group with values from the culvert zones file where culverts exist and from the
    original DEM file everywhere else.
    Parameters
    ----------
    in_dem_path : str
        Path to the DEM input file
    in_zones_path : str
        Path to raster file resulting from zonal statistics minimum tool
    """

    from WBT.whitebox_tools import WhiteboxTools
    wbt = WhiteboxTools()

    out_group = new_group_00(in_dem_path)

    # Create position raster
    pos_path = new_file_00(in_dem_path, "POS", "tif", out_group)
    wbt.is_no_data(in_zones_path, pos_path)

    output_path = new_file_00(in_dem_path, "DEM", "tif", out_group)

    inputs = "{};{}".format(in_zones_path, in_dem_path)

    # If position (isnodata) file = 0, use value from zones. If = 1, use value from dem.
    wbt.pick_from_list(inputs, pos_path, output_path)

    if check_exists_00(output_path):
        return output_path
    else:
        return False


def breach_depressions_00(in_dem_path, breach_dist='20'):
    """Runs whitebox breach_depressions_least_cost tool
    Parameters
    ----------
    in_dem_path : str
        Path to the DEM
    breach_dist : str
        Max distance to breach, in feet.
    """

    from pathlib import Path

    from WBT.whitebox_tools import WhiteboxTools
    wbt = WhiteboxTools()

    out_group = new_group_00(in_dem_path)
    output_path = new_file_00(in_dem_path, "DEM", "tif", out_group)

    wbt.breach_depressions_least_cost(in_dem_path, output_path, breach_dist)

    if check_exists_00(output_path):
        return output_path
    else:
        return False



# === Run all functions === #


def process_dems_00(in_pipe_paths, in_dem_path, extend_dist='20', breach_dist='50'):
    """Create 3 new DSM groups from initial DEM and pipe shapefiles
    For example, from DEM00, the following groups will be created:
    DSM01_DEM00: Burn in culverts
    DSM02_DEM00: Breach depressions
    DSM03_DEM01: Burn in culverts, then breach depressions
    
    Parameters
    ----------
    in_pipe_paths : list
        List of paths to pipe shapefiles (already clipped to basin extent)
    in_dem_path : str
        Path to initial DEM file
    extend_dist : str
        Distance (in feet) to extend the pipe lines from each end
    breach_dist : str
        Maximum distance to breach depressions
    """

    # Add culverts
    merged_pipes = merge_pipes_00(in_pipe_paths)
    extended_pipes = extend_pipes_00(merged_pipes, str(extend_dist))

    pipe_raster = pipes_to_raster_00(extended_pipes, in_dem_path)
    min_zones = zone_min_00(in_dem_path, pipe_raster)
    culverts_dem = burn_min_00(in_dem_path, min_zones)

    # Breach depressions on original DEM file
    breach_depressions_00(in_dem_path, str(breach_dist))

    # Breach depressions on file with culverts
    breach_depressions_00(culverts_dem, str(breach_dist))
