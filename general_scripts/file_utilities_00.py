#! python3
"""
Functions to parse and create file names and paths.


"""


def new_group_00(group_parent_path, grp_str, source_str):
    """
    Parameters
    ----------
    group_parent_path : str
    grp_str : str
    source_str : str

    Returns
    -------
    new_group : object
    """
    
    from pathlib import Path
    
    group_parent = Path(group_parent_path)
    grp_nos = []
    for grp in group_parent.iterdir():
        if grp.is_dir():
            grp_no = grp.name.split("_")[0][-2:]
            grp_nos.append(int(grp_no))
    
    if len(grp_nos) > 0:
        new_grp_no = ('0' + str(max(grp_nos) + 1))[-2:]
    else:
        new_grp_no = '00'
    
    new_group = group_parent.joinpath(
        "{}{}_{}".format(grp_str, new_grp_no, source_str))
    
    new_group.mkdir(parents=True)
    
    return new_group


def new_file_00(in_file_path, name=None, out_ext=None, out_grp_path=None):
    """Create name and path for a new file, based on the path to an input file

    Optional parameters default to the same as the input file.

    Parameters
    ----------
    in_file_path: string
        Path to input file
    name: string
        Example: "DEM"
    out_ext: string
        File extension for the output file. Example: "shp"
    out_grp_path: string
        Path to output directory

    Returns
    -------
    out_file: object
    """
    
    from pathlib import Path
    
    in_file = File(in_file_path)
    huc = in_file.huc
    
    if name is None:
        name = in_file.str
    
    if out_ext is None:
        out_ext = in_file.ext
    
    if out_grp_path is None:
        out_grp = in_file.grp
        out_num = in_file.num
    else:
        out_grp = Path(out_grp_path)
        out_num = out_grp.name.split("_")[0][-2:]
        out_grp.mkdir(parents=True, exist_ok=True)
    
    out_file_name = "{}_{}{}_{}{}.{}".format(huc, name, out_num,
                                             in_file.str, in_file.num, out_ext)
    out_file = out_grp.joinpath(out_file_name)
    
    return out_file

