#!/usr/bin/env python3
""" Runs TauDEM tools

Usage
-----
To create the initial sfw group, run `dem_to_sfw_00`.

To create a stream network group from the files created using the GRASS r.watershed tool, run `watershed_to_snet_00`

"""


def td_cmd_00(tool_args):
    """

    Parameters
    ----------
    tool_args: list
    """

    import subprocess

    cmd = ["mpiexec", "-n", "8"]
    cmd.extend(tool_args)

    subprocess.check_call(cmd)


def pit_remove_00(dem_path):
    """Creates SFW group and FEL file.

    Parameters
    ----------
    dem_path: str
        Path to DEM file

    Returns
    -------
    fel: path object
        FEL file path
    """
    from pathlib import Path

    td_args = ["PitRemove", "-z", str(dem_path)]
    dem = Path(str(dem_path))
    name_strings = dem.stem.split("_")
    in_group_num = name_strings[1][-2:]
    fel = dem.parent.parent.parent / "Surface_Flow" / "SFW{n}_DSM{n}".format(n=in_group_num) / "{h}_FEL{n}_{d}.tif".format(h=name_strings[0], n=in_group_num, d=name_strings[1])
    fel.parent.mkdir(parents=True, exist_ok=True)
    td_args.extend(["-fel", str(fel)])

    td_cmd_00(td_args)

    return fel


def flow_dir_00(fel_path):
    """Creates pointer and slope files.

    Parameters
    ----------
    fel_path: str or path object
        Path to FEL tif

    Returns
    -------
    p: path object
        Pointer file path, as Path object
    """
    from pathlib import Path

    td_args = ["D8FlowDir"]
    fel = Path(str(fel_path))
    p_name = fel.name.replace("FEL", "P").replace("DEM", "FEL")
    s_name = fel.name.replace("FEL", "D8SLP").replace("DEM", "FEL")
    p = fel.parent.joinpath(p_name)
    slp = fel.parent.joinpath(s_name)

    td_args.extend(["-fel", str(fel_path), "-p", str(p), "-sd8", str(slp)])
    td_cmd_00(td_args)

    return p


def area_d8_00(p_path):
    """Creates D8 Area file.

    Parameters
    ----------
    p_path: str
        Path to pointer file, which could be created by TauDEM or r.watershed.

    Returns
    -------
    d8: path object
        D8 Area file
    """
    from pathlib import Path

    td_args = ["AreaD8"]
    p = Path(str(p_path))
    d8_name = p.name.replace("P", "D8AREA").replace("FEL", "P")
    d8 = p.parent / d8_name

    td_args.extend(["-p", str(p_path), "-ad8", str(d8)])
    td_cmd_00(td_args)

    return d8


def grid_net_00(p_path):
    """

    Parameters
    ----------
    p_path: str
        Path to P tif

    Returns
    -------
    dict
        Dictionary of paths to sfw group and files
    """
    from pathlib import Path

    td_args = ["Gridnet", "-p", str(p_path)]

    p = Path(str(p_path))
    sfw = p.parent
    plen_name = p.name.replace("P", "PLEN").replace("FEL", "P")
    tlen_name = p.name.replace("P", "TLEN").replace("FEL", "P")
    gord_name = p.name.replace("P", "GORD").replace("FEL", "P")

    plen = sfw / plen_name
    tlen = sfw / tlen_name
    gord = sfw / gord_name

    td_args.extend(["-plen", str(plen), "-tlen", str(tlen), "-gord", str(gord)])

    td_cmd_00(td_args)

    return dict(
        sfw=sfw,
        plen=plen,
        tlen=tlen,
        gord=gord,
    )


# ============================
# === Run all of the above ===

def dem_to_sfw_00(dem_path):
    """Create SFW group with all TauDEM results.

    Use this to create the first set of SFW groups.

    Parameters
    ----------
    dem_path: str
        Path to DEM .tif file

    Returns
    -------
    sfw: dict
    """

    fel = pit_remove_00(dem_path)
    p = flow_dir_00(fel)
    d8 = area_d8_00(p)
    out_paths = grid_net_00(p)
    out_paths.update(fel=fel, p=p, d8=d8)
    return out_paths


def p_to_sfw_00(p):
    """Starting with a pointer file, creates the rest of the SFW group.

    Use this on the P file exported by `gr_watershed_00`.

    Note
    ----
    This does not create an FEL file. When you run `stream_net_00` or another script with the parameter `fel`, enter the DEM path instead.

    Parameters
    ----------
    p

    Returns
    -------

    """

    d8 = area_d8_00(p)
    out_paths = grid_net_00(p)
    out_paths.update(p=p, d8=d8)
    return out_paths


# ==========================================
#! Not done testing anything below this line


def threshold_00(ssa_path, threshold):
    """

    Parameters
    ----------
    ssa_path : str
        Path to .tif file. Which one depends on the method being used. Could be:
        - FWINVPLAN
        - ORD
        - GORD
    threshold : int
        If running with FWINVPLAN, try 5 for 20ft resolution, 60 for 10ft, 500 for 5ft.
        If running with ORD, 5 usually works.
        If running with D8AREA, default is 100

    Returns
    -------
    src: object

    """

    from pathlib import Path

    from general_scripts import file_utilities_00 as pf

    td_args = ["Threshold", "-ssa", str(ssa_path)]
    ssa = Path(str(ssa_path))
    sp = ssa.parent.parent.parent / "Stream_Pres"
    name_strings = ssa.stem.split("_")
    source_str = name_strings[1]
    huc = name_strings[0]

    group = Path(str(pf.new_group_00(sp, "STPRES", source_str)))

    new_grpno = group.name.split("_")[0][-2:]
    src_name = "{h}_SRC{g}_{s}.tif".format(h=huc, g=new_grpno, s=source_str)
    src = sp.joinpath(group, src_name)

    td_args.extend(["-src", str(src), "-thresh", str(threshold)])
    td_cmd_00(td_args)

    return src


def stream_net_00(fel_path, p_path, ad8_path, src_path):
    """

    Parameters
    ----------
    fel_path : str
        If r.watershed was used to create the P and/or SRC files, use the DEM here instead of the FEL.
    p_path : str
    ad8_path : str
    src_path : str

    Returns
    -------
    dict
        Paths to newly created groups and files
    """
    from pathlib import Path

    from general_scripts import file_utilities_00 as pf

    td_args = ["StreamNet", "-fel", str(fel_path), "-p", str(p_path), "-ad8",
               str(ad8_path), "-src", str(src_path)]

    src = Path(str(src_path))
    prj = src.parent.parent.parent
    name_strings = src.stem.split("_")
    src_str = name_strings[1]
    huc = name_strings[0]

    sn_parent = prj / "Stream_Net"
    sn_parent.mkdir(parents=True, exist_ok=True)
    snet_grp = Path(str(pf.new_group_00(sn_parent, "SNET", src_str)))
    snet_grpno = snet_grp.name.split("_")[0][-2:]
    snet_grp.mkdir(parents=True, exist_ok=True)

    bsn_parent = prj / "Basins"
    bsn_parent.mkdir(parents=True, exist_ok=True)
    bsn_grp = Path(str(pf.new_group_00(bsn_parent, "BSN", src_str)))
    bsn_grpno = bsn_grp.name.split("_")[0][-2:]
    bsn_grp.mkdir(parents=True, exist_ok=True)

    # Name output files
    ord_name = "{h}_ORD{g}_{s}.tif".format(h=huc, g=snet_grpno, s=src_str)
    tree_name = "{h}_TREE{g}_{s}.dat".format(h=huc, g=snet_grpno, s=src_str)
    coord_name = "{h}_COORD{g}_{s}.dat".format(h=huc, g=snet_grpno, s=src_str)
    rch_name = "{h}_RCH{g}_{s}.shp".format(h=huc, g=snet_grpno, s=src_str)
    bsn_name = "{h}_BSN{b}_{s}.tif".format(h=huc, b=bsn_grpno, s=src_str)

    ord = snet_grp / ord_name
    tree = snet_grp / tree_name
    coord = snet_grp / coord_name
    rch = snet_grp / rch_name
    bsn = bsn_grp / bsn_name

    td_args.extend(["-ord", str(ord), "-tree", str(tree), "-coord",
                    str(coord), "-net", str(rch), "-w", str(bsn)])

    if src_str[:-2] is not "ORD":
        td_args.append("-sw")

    td_cmd_00(td_args)

    return dict(
        snet=snet_grp,
        ord=ord,
        tree=tree,
        coord=coord,
        rch=rch,
        bsn=bsn_grp,
    )

######################################################################
# Combined functions
#
######################################################################


def inverse_plan_to_snet_00(invplan_path, threshold, fel, p, d8, src):  # FIXME
    """Creates flow weighted, stream src, & stream net groups from planform.

    """

    src = threshold_00(str(invplan_path), threshold)
    rch = stream_net_00(str(fel), str(p), str(d8), str(src))

    return dict(src=src, rch=rch)


def watershed_to_snet_00(dem_path, p_path, src_path):
    """Creates SNET group and RCH network from GRASS r.watershed results and related DEM.

    Parameters
    ----------
    dem_path : str
        Path to the dem used to run the watershed tool
    p_path : str
        Path to the P file exported from GRASS
    src_path : str
        Path to the SRC file exported from GRASS

    Returns
    -------
    out_paths : dict
    """

    fel = pit_remove_00(dem_path)
    d8_area = area_d8_00(p_path)
    out_paths = stream_net_00(fel, p_path, d8_area, src_path)

    out_paths.update(fel=fel, d8=d8_area)

    return out_paths
