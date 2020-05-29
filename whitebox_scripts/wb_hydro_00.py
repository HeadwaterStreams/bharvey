#! python3
"""
Create hydro-enforced DEMs

From initial DEM and culvert shapefiles, create 3 new DSM groups:
- DEM with culverts
- DEM with breached depressions
- DEM with culverts and breached depressions

Basic Usage:
To create all DSM groups for 20ft resolution, on the first run, use
process_dems_first_00([pipe files], dem_path)
If you have a rasterized pipe zones file, use process_dems_00(pipe_zones_path,
dem_path)

Updated: 2020-04-07
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
    
    if len(grps) > 0:
        grpnos = []
        for g in grps:
            new_mo = grpRegex.search(g)
            grpno = new_mo.group(2)
            grpnos.append(int(grpno))
        out_grpno = ('0' + str(max(grpnos) + 1))[-2:]
    else:
        out_grpno = '00'
    
    out_grp = "{}{}_{}{}".format(grp_name, out_grpno, source_str, in_grpno)
    out_grp_path = os.path.join(in_grp_parent, out_grp)
    os.makedirs(out_grp_path)
    
    return out_grp_path


def new_group_01(folder_path, source, name=None):
    """Create the next group in the folder
    
    Parameters
    ----------
    folder_path : str or path object
        Path to parent folder. Example: r'D:\...\Basins\CHOWN05\Surface'
        It does not have to exist.
    source : str
        Name substring for the source file or folder. Example: 'DEM00'
    name : str, optional
        Name substring for the new group. Example: 'DSM'
        Only needed if there are no existing groups in the parent folder.

    Returns
    -------
    new_group : str
        Path to new group
    """

    from pathlib import Path
    
    folder = Path(str(folder_path))
    num = '00'
    
    if folder.exists():
        flist = [f for f in folder.iterdir() if f.is_dir()]
        if len(flist) > 0:
            grpnos = []
            for grp in flist:
                grpno = int(grp.name.split('_')[0][-2:])
                grpnos.append(grpno)
                name = grp.name.split('_')[0][:-2]
            num = ('0' + str(max(grpnos) + 1))[-2:]
    
    new_group_name = "{}{}_{}".format(name, num, source)
    new_group = folder.joinpath(new_group_name)
    new_group.mkdir(parents=True)
    
    return str(new_group)


def new_file_00(in_file_path, name, out_ext, out_grp_path=None):
    """
    Parameters
    ----------
    in_file_path: str or path object
        Path to input file
    name: str
        Example: "DEM"
    out_ext: str
        File extension for the output file. Example: "shp"
    out_grp_path: str or path object
        Path to output directory. If none given, uses input directory.
    """
    from pathlib import Path
    
    in_file = Path(str(in_file_path))
    in_grp = in_file.parent
    name_strings = in_file.stem.split('_')
    huc = name_strings[0]
    source = name_strings[1]
    in_grpno = source[-2:]
    
    if out_grp_path is not None:
        out_grp = Path(out_grp_path)
        out_grpno = out_grp.stem.split('_')[0][-2:]
    else:
        out_grp = in_grp
        out_grpno = in_grpno
    
    out_file_name = "{}_{}{}_{}.{}".format(huc, name, out_grpno,
                                           source, out_ext)
    out_file_path = out_grp / out_file_name
    
    return str(out_file_path)


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


def clip_pipes_00(in_pipe_path, dem_path):
    """Clip statewide culvert shapefile to DEM extent

    Parameters
    ----------
    in_pipe_path : string
        Path to full culvert file
    dem_path : str
        Path to DEM file

    Returns
    -------
    out_file : str
        Path to clipped file
    """
    
    from pathlib import Path
    
    from WBT.whitebox_tools import WhiteboxTools
    
    wbt = WhiteboxTools()
    
    dem = Path(dem_path)
    source_string = dem.stem.split("_")[0]
    huc_dir = dem.parent.parent.parent
    box = new_file_00(dem_path, "BOX", ".shp")
    
    # Create vector bounding box
    wbt.layer_footprint(dem_path, str(box))
    
    # Create new pipe group
    pipe_group = new_group_01(str(huc_dir / "Hydro_Route"),
                              source_string,
                              "PIPES")
    out_file = new_file_00(dem_path, "PIPES", "shp", pipe_group)
    
    # Clip pipe file to bounding box
    wbt.clip(in_pipe_path, str(box), str(out_file))
    
    return out_file


def merge_pipes_00(in_pipe_paths):
    """ Merge culvert features from multiple files and save to a new
    Hydro_Route group
    
    Parameters
    ----------
    in_pipe_paths : list
        List of pipe files to merge. Pipe files should already be clipped to
        basin extent. (If not, run extract_pipes_00 first.)
        
    Returns
    -------
        Path to merged pipe file, in new Hydro_Route group
    """
    from pathlib import Path
    
    from WBT.whitebox_tools import WhiteboxTools
    
    wbt = WhiteboxTools()
    
    last_pipe = Path(in_pipe_paths[-1])
    
    out_group = new_group_01(str(last_pipe.parent.parent),
                             last_pipe.stem.split('_')[1], "PIPES")
    output_path = new_file_00(str(last_pipe), "PIPES", "shp",
                              str(out_group))
    
    wbt.merge_vectors(';'.join(in_pipe_paths), output_path)
    
    if check_exists_00(output_path):
        return output_path
    else:
        return False


def extend_pipes_00(in_pipe_path, dist='20.0'):
    """ Extend individual culvert lines at each end, by the specified distance

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
    """Convert the pipes feature to a raster. Lines will be 1 cell wide.

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
    wbt.vector_lines_to_raster(in_pipe_path, output_path, field="FID",
                               nodata=True,
                               base=in_dem_path)
    
    if check_exists_00(output_path):
        return output_path
    else:
        return False


def zone_min_00(in_dem_path, in_zones_path):
    """
    Set cells in culvert zones to the min elevation for the zone

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
    wbt.zonal_statistics(in_dem_path, in_zones_path, output_path,
                         stat="minimum", out_table=None)
    
    if check_exists_00(output_path):
        return output_path
    else:
        return False


def burn_min_00(in_dem_path, in_zones_path):
    """Create DEM with culvert zones burned in

    Uses culvert zone min values where culvert zones exist and values from the
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
    
    # If position (isnodata) file = 0, use value from zones. If = 1,
    # use value from dem.
    wbt.pick_from_list(inputs, pos_path, output_path)
    
    if check_exists_00(output_path):
        return output_path
    else:
        return False


def breach_depressions_00(in_dem_path, breach_dist='20'):
    """Run whitebox breach_depressions_least_cost tool

    Parameters
    ----------
    in_dem_path : str
        Path to the DEM
    breach_dist : str
        Search radius
    """
    
    from WBT.whitebox_tools import WhiteboxTools
    
    wbt = WhiteboxTools()
    
    out_group = new_group_00(in_dem_path)
    output_path = new_file_00(in_dem_path, "DEM", "tif", out_group)
    
    wbt.breach_depressions_least_cost(in_dem_path, output_path, breach_dist,
                                      fill=True)
    # TODO: add max_cost parameter for DEMs with quarries
    
    if check_exists_00(output_path):
        return output_path
    else:
        return False


def fill_and_breach_zones_00(old_dem, new_dem, min_depth=0.1): #FIXME
    """Create polygons for fill zones and breaches

     Compares original vs post-breach-depressions DEM elevations. For any
     cells where the difference exceeds min_depth, a polygon is created.

    Parameters
    ----------
    old_dem : str or object
        Path to original DEM
    new_dem : str or object
        Path to new DEM created with breach_depressions
    min_depth : float or str
        Minimum difference between DEMs, in feet
    """
    from WBT.whitebox_tools import WhiteboxTools
    wbt = WhiteboxTools()

    # Create difference raster
    diff = new_file_00(new_dem, 'DIFF', 'tif')
    wbt.subtract(str(new_dem), str(old_dem), diff)

    #############
    # Fill Zones
    #############
    
    # Create patches where new_dem > old_dem
    fill_cells = new_file_00(diff, 'FCEL', 'tif')
    f_patch_vals = '0;min;{d};1;{d};max'.format(d=min_depth)
    wbt.reclass(diff, fill_cells, f_patch_vals)

    # Clump contiguous fill zone cells
    fill_clumps = new_file_00(fill_cells, 'FCLMP', 'tif')
    wbt.clump(fill_cells, fill_clumps, diag=True, zero_back=True)

    # Find area of clumps
    clump_area = new_file_00(fill_clumps, 'FAREA', 'tif')
    wbt.raster_area(fill_clumps, clump_area, out_text=False, units="grid cells",
                    zero_back=True)
    # Remove single-cell clumps
    multi_cell = new_file_00(clump_area, 'FPTCH', 'tif')
    patch_area_vals = '0;min;2;1;2;max'
    wbt.reclass(clump_area, multi_cell, patch_area_vals)
    wbt.modify_no_data_value(multi_cell, "0")

    # Clump contiguous cells again
    fill_zones = new_file_00(multi_cell, 'FZ', 'tif')
    wbt.clump(multi_cell, fill_zones, diag=True, zero_back=True)

    # Zonal stats
    means = new_file_00(diff, 'FMEAN', 'tif')
    wbt.zonal_statistics(diff, fill_zones, means, stat="mean")

    # Raster to polygon
    fill_poly = new_file_00(means, 'FP', 'shp')
    wbt.raster_to_vector_polygons(means, fill_poly)
    # Add area field
    wbt.polygon_area(fill_poly)




#########################################################################
# === Combined functions ===


def process_culverts_00(culvert_paths, in_dem_path, extend_dist='20'):
    """
    
    Parameters
    ----------
    culvert_paths : list
        Paths to culvert files. This should work with shapefiles either
        statewide or extracted to the basin.
    in_dem_path : str
        Path to first DEM file
    extend_dist : str
        Distance to extend pipes from each end
        
    Returns
    -------
    pipe_raster : str
        Path to raster created from clipped, merged pipe files
    """
    from pathlib import Path

    huc = Path(in_dem_path).stem.split("_")[0]
    
    pipes = []
    for cp in culvert_paths:
        if huc not in cp:
            clip = clip_pipes_00(cp, in_dem_path)
            pipes.append(clip)
        else:
            pipes.append(cp)
    
    merged_pipes = merge_pipes_00(pipes)
    extended_pipes = extend_pipes_00(merged_pipes, str(extend_dist))
    pipe_raster = pipes_to_raster_00(extended_pipes, in_dem_path)
    
    return pipe_raster


def process_dems_00(pipe_zones_path, in_dem_path, breach_dist='50'):
    """Create 3 new DSM groups from initial DEM and pipe zones raster.
    If you already have the pipe zones file from the first run, start here.
    If not, run process_dems_first_00() on the 20-ft resolution DEM first.

    For example, from DEM00, the following groups will be created:
    DSM01_DEM00: Burn in culverts
    DSM02_DEM00: Breach depressions
    DSM03_DEM01: Burn in culverts, then breach depressions
    
    Parameters
    ----------
    pipe_zones_path : str
        Path to pipe zone .tif file (created from first run)
    in_dem_path : str
        Path to initial DEM file
    breach_dist : str
        Maximum distance to breach depressions

    Returns
    -------
    dems : list
        List of paths to DEM files (useful if called from another script)
    """
    
    dems = [in_dem_path]
    
    # Add culverts to DEM
    min_zones = zone_min_00(in_dem_path, pipe_zones_path)
    dem01 = burn_min_00(in_dem_path, min_zones)
    dems.append(dem01)
    
    # Breach depressions on original DEM file
    dem02 = breach_depressions_00(in_dem_path, str(breach_dist))
    dems.append(dem02)
    
    # Breach depressions on file with culverts
    dem03 = breach_depressions_00(dem01, str(breach_dist))
    dems.append(dem03)
    
    return dems


def process_dems_first_00(culvert_paths, in_dem_path, extend_dist='20',
                          breach_dist='50'):
    """Create next 3 DEMs from initial DEM and pipe shapefiles
    
    You only need to run this once, preferably using a 20ft resolution DEM.
    If you already have a rasterized culvert file for the basin,
    use process_dems_00()

    Parameters
    ----------
    culvert_paths : list
        List of paths to culvert .shp files
    in_dem_path : str
        Path to initial DEM
    extend_dist : str
        Distance in feet to extend culvert lines from each end
    breach_dist : str
        Max breach distance, in feet

    Returns
    -------
    dems : list
        List of paths to DEM files (useful if called from another script)
    """
    
    pipe_raster = process_culverts_00(culvert_paths, in_dem_path, extend_dist)
    dems = process_dems_00(pipe_raster, in_dem_path, breach_dist)
    
    return dems
