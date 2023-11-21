import os
import math
import argparse
import pprint



# Uses the passed directory to determine the workload categories and workloads.
#    Assumes that the directory contains directories which name the workload
#    categories and the directories contain the workloads.
def determine_workloads(dir: str) -> dict[str, list[str]]:

    # A workload category is a name in the filebench_workloads directory.
    #    At the time of writing, categories include: "file-server", "files-cr", etc.
    workload_categories: list[str] = []
    
    # A workload is the name of a filebench workload (a .f file).
    # Maps a workload category to a list of workloads.
    workloads: dict[str, list[str]] = {}

    subdir_cnt = +math.inf
    for i, (root, dirs, files) in enumerate(os.walk(dir, True)):
        if i == 0:
            assert(len(files) == 0)
            subdir_cnt = len(dirs)
            workload_categories = dirs
        elif i > subdir_cnt:
            raise AssertionError("The directory should be 2-leveled.")
        else:
            assert(len(dirs) == 0)
            workloads[root] = files

    return workloads  



# Pretty printing of workloads for user's viewing pleasure.
def print_workloads(workloads: dict[str, list[str]]) -> None:

    for key in workloads:
        print("For category " + os.path.basename(key) + " we have the following workloads: ")
        print(workloads[key])
        print()



# Build the argument parser for this program.
def build_argparser() -> argparse.ArgumentParser:

    parser = argparse.ArgumentParser(description="Options for filebench tests.")

    parser.add_argument("device_mountpoint", help="The directory on which the filesystem \
                        will live. If you don't use a userspace filesystem, the \
                        filebench tests will operate on this directory directly. If \
                        you do use a userspace filesystem, this directory will serve \
                        as the physical storage for the userspace filesystem, and \
                        the filebench tests will operate on the directory specified \
                        by the stackfs_mountpoint argument. In any case, this \
                        device will be wiped and reformatted before every filebench \
                        workload.", action='store')

    parser.add_argument("--stackfs_mountpoint", help="The mountpoint for the StackFS \
                        userspace filesystem. If this argument is not specified, \
                        the kernel-based filesystem is used.", required=False, 
                        action='store')

    parser.add_argument("--stackfs_opt", help="Flag indicating if the optimized version of \
                        the StackFS userspace filesystem should be used or not. Does \
                        not do anything if a userspace filesystem is not used.",
                        required=False, default=False, action='store_true')

    filebench_group = parser.add_mutually_exclusive_group(required=True)

    filebench_group.add_argument("--filebench_category", help="The category of filebench tests \
                                 to run.", action='store')

    filebench_group.add_argument("--filebench_test", help="A particular filebench test to \
                                 run.", action='store')

    parser.add_argument("--modified_glibc", help="Location of the .so file containing \
                        the modified glibc. If this argument is specified, the filebench \
                        executable is linked against this modifed glibc. If this argument \
                        is not specified, the system glibc is used.", required=False,
                        action='store')

    parser.add_argument("stats_dir", help="Directory in which the statistics produced \
                        by the filebench tests should be dumped.", action='store')

    return parser



if __name__ == "__main__":

    # Let the user know which workloads are available. 
    """
    FILEBENCH_WORKLOAD_DIR_NAME = "filebench_workloads"
    filebench_workload_dir_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), FILEBENCH_WORKLOAD_DIR_NAME)
    workloads = determine_workloads(filebench_workload_dir_path)
    print_workloads(workloads)
    """

    # Parse the arguments passed to this program.
    parser = build_argparser()
    args = parser.parse_args()
    print(args)


    









