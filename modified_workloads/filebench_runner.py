import os
import math
import argparse
import pprint
from typing import Any
import subprocess
import time



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

    parser.add_argument("backing_store", help="The storage in which the filesystem \
                        will live. This could be the path to a disk partition or \
                        the path to a normal file. In any case, this \
                        partition/file will be wiped and reformatted before every filebench \
                        workload.", action='store')
    
    parser.add_argument("backing_store_mountpoint", help="The desired mountpoint \
                        for the filesystem which lives in the backing store. If \
                        StackFS is not used, the filebench tests will always operate \
                        on this directory. If StackFS is used, the filebench tests \
                        operate on the mounted userspace filesystem (aka the stackfs_\
                        mountpoint).", action='store')

    stackfs_group = parser.add_argument_group("stackfs")

    stackfs_group.add_argument("--use_stackfs", help="Flag which indicates if the user \
                               wants to use the StackFS userspace filesystem.", 
                               required=False, action='store_true')

    stackfs_group.add_argument("--stackfs_mountpoint", help="The mountpoint for the StackFS \
                               userspace filesystem. Must be passed if the StackFS is to \
                               be used.", required=False, action='store')

    stackfs_group.add_argument("--stackfs_binary", help="The path to the StackFS binary. \
                               Must be passed if the StackFS is to be used.", 
                               required=False, action='store')

    stackfs_group.add_argument("--stackfs_opt", help="Flag indicating if the optimized version of \
                               the StackFS userspace filesystem should be used or not. Does \
                               not do anything if stackfs is not used.",
                               required=False, default=False, action='store_true')

    filebench_group = parser.add_mutually_exclusive_group(required=True)

    filebench_group.add_argument("--filebench_category", help="The category of \
                                 filebench tests to run. Should be the name of a \
                                 directory in the filebench_workloads directory.", 
                                 action='store')

    filebench_group.add_argument("--filebench_test", help="A particular filebench test to \
                                 run. Should be the path to a .f file.", action='store')

    parser.add_argument("--modified_glibc", help="Location of the .so file containing \
                        the modified glibc. If this argument is specified, the filebench \
                        executable is linked against this modifed glibc. If this argument \
                        is not specified, the system glibc is used.", required=False,
                        action='store')

    parser.add_argument("stats_dir", help="Directory in which the statistics produced \
                        by the filebench tests should be dumped.", action='store')

    return parser


def sanity_check_args(args: dict[str, Any]) -> None:

    if not os.path.exists(args["backing_store"]):
        raise AssertionError("Bad path to backing store.")

    if not os.path.exists(args["backing_store_mountpoint"]):
        raise AssertionError("Bad path to backing store mountpoint.")

    if args["use_stackfs"]:
        if (args["stackfs_mountpoint"] is None) or (args["stackfs_binary"] is None):
            raise AssertionError("When using StackFS, you need to specify a mountpoint \
                                 and the binary.")
        if not os.path.exists(args["stackfs_mountpoint"]):
            raise AssertionError("That StackFS mountpoint does not exist!")
        if not os.path.exists(args["stackfs_binary"]):
            raise AssertionError("That StackFS binary does not exist!")

    if args["filebench_category"] is not None:
        FILEBENCH_WORKLOAD_DIR_NAME = "filebench_workloads"
        filebench_workload_dir_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), FILEBENCH_WORKLOAD_DIR_NAME)
        workloads = determine_workloads(filebench_workload_dir_path)

        if args["filebench_category"] not in workloads:
            raise AssertionError("That filebench category does not exist!") 
    elif args["filebench_test"] is not None:
        if not os.path.exists(args["filebench_test"]):
            raise AssertionError("That filebench test doesn't exist!")

    if args["modified_glibc"] is not None:
        if not os.path.exists(args["modified_glibc"]):
            raise AssertionError("The modified glibc does not exist!")

    if not os.path.exists(args["stats_dir"]):
        raise AssertionError("The statistics directory does not exist!")

    return 0



# Reformat a backing store.
# The argument size is in units of kilobytes.
# Using the same settings as the "To FUSE or Not to FUSE" paper.
def reformat_backing_store(store: str, size: int=5000) -> None:

    subprocess.run(["rm", "-rf", store])
    subprocess.run(["touch", store])
    subprocess.run(["mke2fs", "-F", "-q", "-E", "lazy_itable_init=0,lazy_journal_init=0", 
                    "-t" ,"ext4", store, str(size)], check=True, stdout=subprocess.DEVNULL)
    print("Finished formatting the storage device located at " + store + " with size " + str(size) + " KB.\n")



# Unmount some filesystem.
def unmount_fs(mountpoint: str) -> None:

    subprocess.run(["sudo", "umount", mountpoint], check=True, stdout=subprocess.DEVNULL)
    print("Unmounted the mountpoint " + mountpoint + ".\n")



# Mount a filesystem contained in some backing store to some mountpoint.
def mount_fs(mountpoint: str, backing_store: str) -> None:

    subprocess.run(["sudo", "mount", "-t", "ext4", backing_store, mountpoint], check=True, stdout=subprocess.DEVNULL)

    # Allow all users to access this mounted filesystem.
    subprocess.run(["sudo", "chmod", "-R", "777", mountpoint], check=True, stdout=subprocess.DEVNULL)

    print("Mounted the filesystem with backing store " + backing_store + " at mountpoint " + mountpoint + ".\n")



# Do miscellaneous stuff like flushing caches, etc. before every filebench test.
def prepare_for_test() -> None:

    subprocess.run(["sync"], check=True)

    with open("/proc/sys/vm/drop_caches", "w") as outfile:
        subprocess.run(["echo", "3"], stdout=outfile, check=True)

    print("Finished preparing for tests.\n")



# Start the userspace filesystem daemon and mount the userspace filesystem to
#    somewhere.
def start_userspace_fs(underlying_fs_mountpoint: str, userspace_fs_mountpoint: str, opt: bool) -> None:
    return



# Kill the userspace filesystem daemon and unmount the userspace filesystem.
def teardown_userspace_fs(fs_daemon_pid: int, userspace_fs_mountpoint: str) -> None:
    return



# Slightly hacky.
# For a particular filebench workload (.f file), set the target directory on which
#    the filebench workload will operate. This function modifies the content of 
#    the .f file.
def set_filebench_target_dir(file: str, target_dir: str) -> None:

    # This is a bit hacky.
    # In the filebench workload file, it's necessary to specify the target directory
    #    for the filebench tests.
    # If you look at the top of every .f file in the filebench_workloads directory,
    #    you'll see that the first line is "$dir=". This means that the target
    #    directory is unspecified.
    # This function is responsible for replacing that first line so that the target
    #    directory can be specified at runtime.

    all_file_lines = None 
    SPECIAL_FIRST_LINE = "set $dir="     
    with open(file, "r+") as test_file:

        # Check that the first characters are as expected. 
        first_line = test_file.read(len(SPECIAL_FIRST_LINE))

        if first_line != SPECIAL_FIRST_LINE:
            raise AssertionError("The first line of the filebench test with name " + \
                                 test + " did not start with the special sequence " + \
                                 SPECIAL_FIRST_LINE)

        # Save all the lines in the file.
        test_file.seek(0, 0)
        all_file_lines = test_file.readlines() 

    with open(file, "w+") as test_file:

        for line in all_file_lines:
            if line == SPECIAL_FIRST_LINE + "\n":
                new_first_line = SPECIAL_FIRST_LINE + target_dir + "\n"
                test_file.write(new_first_line)
            else:
                test_file.write(line)



def run_filebench_command(test: str, stats_dir: str, modified_glibc: str=None) -> None:

    stats_file_name = os.path.basename(test) + "_" + str(time.time())
    stats_file_path = os.path.join(stats_dir, stats_file_name)
    stats_file = open(stats_file_path, "x")

    print("Starting test " + test + "\n")
    print("Writing the results of this test to " + stats_file_path + "\n")
    subprocess.run(["filebench", "-f", test], stdout=stats_file, check=True)
    print("Finished test " + test + "\n")



# Run a single filebench test.
# All arguments should be absolute paths to directories or files. 
def run_test(test: str, backing_store: str, backing_store_mountpoint: str, 
             stats_dir: str, modified_glibc: str=None) -> None:

    # Set the directory on which the filebench test will operate. 
    set_filebench_target_dir(test, backing_store_mountpoint)

    # Reformat the underlying storage medium and mount it.
    reformat_backing_store(backing_store)
    mount_fs(backing_store_mountpoint, backing_store)

    prepare_for_test() 

    run_filebench_command(test, stats_dir, modified_glibc)

    # Unmount the filesystem.
    unmount_fs(backing_store_mountpoint)



if __name__ == "__main__":

    # Parse and sanity check the passed arguments. 
    parser = build_argparser()
    args = vars(parser.parse_args())
    sanity_check_args(args)

    # Now switch on the passed arguments to do the stuff the user wants.
    if (not args["use_stackfs"]) and (args["filebench_test"] is not None):
        run_test(args["filebench_test"], args["backing_store"], args["backing_store_mountpoint"],
                 args["stats_dir"])
    else:
        print("Can't handle that particular set of arguments right now...")

