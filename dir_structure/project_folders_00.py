#! python3
"""



"""

# TODO: Rewrite these to use pathlib, clean up any unnecessary stuff, make them more versatile.


def new_group_00(group_parent_path, grp_str, source_str):
    """
    Parameters
    ----------
    group_parent_path : str
    grp_str : str
    source_str : str
    """

    from pathlib import Path

    group_parent = Path(group_parent_path)

    grps = group_parent.glob(grp_str + '*')  # TODO: Make this a list comprehension, filter to only dirs

    if grps:
        grp_nos = []
        for grp in grps:  # TODO: Make this a list comprehension
            grp_no = grp.name.split("_")[0][-2:]
            grp_nos.append(int(grp_no))

        new_grp_no = ('0' + str(max(grp_nos) + 1))[-2:]
    else:
        new_grp_no = '00'

    new_group = group_parent.joinpath("{}{}_{}".format(grp_str, new_grp_no, source_str))

    Path.mkdir(new_group)

    return new_group


def out_file_00(in_file_path, name, out_ext, out_grp_path=None):
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
        Path to output directory. If none given, same as input directory.
    """

    from pathlib import Path

    in_file = Path(in_file_path)
    in_grp = in_file.parent

    name_strings = in_file.name.split("_")
    huc = name_strings[0]
    source_name = name_strings[1][:-2]
    in_grpno = name_strings[1][-2:]

    if out_grp_path is not None:
        out_grp = Path(out_grp_path)
        out_grpno = out_grp.name.split("_")[0][-2:]

    else:
        out_grp = in_grp
        out_grpno = in_grpno

    out_file_name = "{}_{}{}_{}{}.{}".format(huc, name, out_grpno, source_name, in_grpno, out_ext)
    out_file_path = out_grp.joinpath(out_file_name)

    return out_file_path
