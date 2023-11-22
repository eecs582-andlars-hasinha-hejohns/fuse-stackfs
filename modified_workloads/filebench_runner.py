"""
This file provides a CLI-based runner for executing filebench workloads on arbitrary
   userspace filesystems and in-kernel filesystems.

Beware, this file should be executed with superuser privleges and does some dangerous
   stuff. In particular, it overwrites specific files, mounts and unmounts certain
   filesystems, clears caches, etc.

Right now, the functionality is not fully general. It is assumed that ext4 should
   be used as the filesystem for the backing store and that the StackFS filesystem
   will be used. To allow arbitrary userspace filesystems to be used, it should only 
   be necessary to modify the start_userspace_fs() function.
"""


import os
import math
import argparse
import pprint
from typing import Any
import subprocess
import time
import tempfile


# Figure out the valid workload categories.
# Makes assumptions about the relative position of this file with respect to the
#    workload directory.
def determine_workloads() -> dict[str, list[str]]:

    FILEBENCH_WORKLOAD_DIR_NAME = "filebench_workloads"
    filebench_workload_dir_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), FILEBENCH_WORKLOAD_DIR_NAME)
    return find_workloads(filebench_workload_dir_path)



# Uses the passed directory to determine the workload categories and workloads.
#    Assumes that the directory contains directories which name the workload
#    categories and the directories contain the workloads.
def find_workloads(dir: str) -> dict[str, list[str]]:

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
    
    return



# Build the argument parser for this program.
def build_argparser() -> argparse.ArgumentParser:

    parser = argparse.ArgumentParser(description="ALL PATHS SHOULD BE ABSOLUTE.")

    parser.add_argument("backing_store", help="The storage in which the filesystem \
                        will live. This could be the path to a disk partition or \
                        the path to a normal file. In any case, this \
                        partition/file will be wiped and reformatted before every filebench \
                        workload.", action='store')
    
    parser.add_argument("backing_store_mountpoint", help="The desired mountpoint \
                        for the filesystem which lives in the backing store. If \
                        a userspace filesystem is not used, the filebench tests will always operate \
                        on this directory. If a userspace filesystem is used, the filebench tests \
                        operate on the mounted userspace filesystem.", action='store')

    stackfs_group = parser.add_argument_group("Userspace Filesystem")

    stackfs_group.add_argument("--use_userspace_fs", help="Flag which indicates if the user \
                               wants to use the userspace filesystem.", 
                               required=False, action='store_true')

    stackfs_group.add_argument("--userspace_fs_mountpoint", help="The mountpoint for the \
                               userspace filesystem. Must be passed if the userspace filesystem is to \
                               be used.", required=False, action='store')

    stackfs_group.add_argument("--userspace_fs_binary", help="Path to the userspace filesystem daemon binary. \
                               Must be passed if the userspace filesystem is to be used.", 
                               required=False, action='store')

    stackfs_group.add_argument("--userspace_fs_opt", help="Flag indicating if the optimized version of \
                               the userspace filesystem should be used or not.", required=False, 
                               default=False, action='store_true')

    filebench_group = parser.add_mutually_exclusive_group(required=True)

    filebench_group.add_argument("--filebench_category", help="The category of \
                                 filebench tests to run. Should be the path to a \
                                 directory in the filebench_workloads directory.", 
                                 action='store')

    filebench_group.add_argument("--filebench_test", help="Path to .f file. A \
                                 particular filebench test to run.", action='store')

    parser.add_argument("--modified_glibc", help="Path to the .so file containing \
                        the modified glibc. If this argument is specified, the filebench \
                        executable is linked against this modifed glibc. If this argument \
                        is not specified, the system glibc is used. Note that you can \
                        choose to use a modified glibc without using a userspace filesystem.",
                        required=False, action='store')

    parser.add_argument("stats_dir", help="Directory in which the statistics produced \
                        by the filebench tests should be dumped.", action='store')

    return parser


def sanity_check_args(args: dict[str, Any]) -> None:

    if not os.path.exists(args["backing_store"]):
        raise AssertionError("Bad path to backing store.")

    if not os.path.exists(args["backing_store_mountpoint"]):
        raise AssertionError("Bad path to backing store mountpoint.")

    if args["use_userspace_fs"]:
        if (args["userspace_fs_mountpoint"] is None) or (args["userspace_fs_binary"] is None):
            raise AssertionError("When using a userspace filesystem, you need to \
                                 specify a mountpoint and the binary.")
        if not os.path.exists(args["userspace_fs_mountpoint"]):
            raise AssertionError("That userspace mountpoint does not exist!")
        if not os.path.exists(args["userspace_fs_binary"]):
            raise AssertionError("That userspace daemon binary does not exist!")

    if args["filebench_category"] is not None:
        workloads = determine_workloads()
        if args["filebench_category"] not in workloads:
            print_workloads(workloads)
            raise AssertionError("That filebench category does not exist!") 
    elif args["filebench_test"] is not None:
        if not os.path.exists(args["filebench_test"]):
            raise AssertionError("That filebench test doesn't exist!")

    if args["modified_glibc"] is not None:
        if not os.path.exists(args["modified_glibc"]):
            raise AssertionError("The modified glibc does not exist!")

    if not os.path.exists(args["stats_dir"]):
        raise AssertionError("The statistics directory does not exist!")

    return



# Reformat a backing store.
# The argument size is in units of kilobytes.
# Using the same settings as the "To FUSE or Not to FUSE" paper.
def reformat_backing_store(store: str, size: int=20000) -> None:

    subprocess.run(["rm", "-rf", store])
    subprocess.run(["touch", store])
    subprocess.run(["mke2fs", "-F", "-q", "-E", "lazy_itable_init=0,lazy_journal_init=0", 
                    "-t" ,"ext4", store, str(size)], check=True, stdout=subprocess.DEVNULL)
    print("Finished formatting the storage device located at " + store + " with size " + str(size) + " KB.\n")
    
    return



# Unmount some filesystem.
def unmount_fs(mountpoint: str) -> None:

    subprocess.run(["sudo", "umount", mountpoint], check=True, stdout=subprocess.DEVNULL)

    print("Unmounted the mountpoint " + mountpoint + ".\n")

    return



# Mount a filesystem contained in some backing store to some mountpoint.
def mount_fs(mountpoint: str, backing_store: str) -> None:

    subprocess.run(["sudo", "mount", "-t", "ext4", backing_store, mountpoint], check=True, stdout=subprocess.DEVNULL)

    # Allow all users to access this mounted filesystem.
    subprocess.run(["sudo", "chmod", "-R", "777", mountpoint], check=True, stdout=subprocess.DEVNULL)

    print("Mounted the filesystem with backing store " + backing_store + " at mountpoint " + mountpoint + "\n")

    return



# Do miscellaneous stuff like flushing caches, etc. right before a filebench
#    test. This function should be called right before starting a test. 
def prepare_for_test() -> None:

    subprocess.run(["sync"], check=True)

    with open("/proc/sys/kernel/randomize_va_space", "r+") as f:
        if int(f.read(1)) != 0:
            print("It was detected that you have virtual address space randomization turned on. This \
                  generally causes the Filebench executable to be non-functioning.")
            subprocess.run(["echo", "0"], stdout=outfile, check=True)
            print("Virtual address space randomization was just turned off.")

    with open("/proc/sys/vm/drop_caches", "w") as outfile:
        subprocess.run(["echo", "3"], stdout=outfile, check=True)

    print("Finished preparing for tests.\n")

    return



# Start the userspace filesystem daemon and mount the userspace filesystem somewhere.
# Returns a Popen object for the group of processes started.
def start_userspace_fs(userspace_fs_binary: str, underlying_fs_mountpoint: str, 
                       userspace_fs_mountpoint: str, opt: bool) -> int:

    # Note that this is non-blocking and starts two processes. The processes
    #    both live in a process group.
    if not opt:
        proc = subprocess.Popen([userspace_fs_binary, "-r", underlying_fs_mountpoint, 
                                 userspace_fs_mountpoint, "-s", "-f"], stdout=subprocess.DEVNULL,
                                 process_group=0)
    else:
        # Mimic the optimizations in the "To FUSE or Not to FUSE" Paper
        raise AssertionError("Optimizations for userspace filesystem not currently supported.")

    print("Started the userspace filesystem daemon and mounted it to " + userspace_fs_mountpoint + "\n")

    return proc



# Kill the userspace filesystem daemon and unmount the userspace filesystem.
def teardown_userspace_fs(popen: subprocess.Popen, userspace_fs_mountpoint: str) -> None:

    popen.kill()

    subprocess.run(["fusermount3", "-u", userspace_fs_mountpoint], stdout=subprocess.DEVNULL, check=True)

    print("Killed the userspace filesystem daemon.\n")

    return



# For a particular filebench workload (.f file), set the target directory on which
#    the filebench workload will operate.
# This function creates a temporary copy of the filebench workload, modifies it 
#    to set the target directory, and returns it. 
def set_filebench_target_dir(file: str, target_dir: str) -> tempfile.NamedTemporaryFile:

    # In the filebench workload file, it's necessary to specify the target directory
    #    for the filebench tests.
    # If you look at the top of every .f file in the filebench_workloads directory,
    #    you'll see that the first line is "$dir=". This means that the target
    #    directory is unspecified.
    # This function is responsible for replacing that first line so that the target
    #    directory can be specified at runtime. But we don't want to modify the .f
    #    file directly, so we instead copy it into a temporary file and use the
    #    temporary file.

    all_file_lines = None 
    SPECIAL_FIRST_LINE = "set $dir="     
    with open(file, "r") as test_file:

        # Check that the first characters are as expected. 
        first_line = test_file.read(len(SPECIAL_FIRST_LINE))

        if first_line != SPECIAL_FIRST_LINE:
            raise AssertionError("The first line of the filebench test with name " + \
                                 test + " did not start with the special sequence " + \
                                 SPECIAL_FIRST_LINE)

        # Save all the lines in the file.
        test_file.seek(0, 0)
        all_file_lines = test_file.readlines() 

    # Create a named temporary file which is a copy of the target file and lives in
    #    the same directory as the target file.
    # Note that this file is closed and deleted as soon as it is garbage collected.
    temp = tempfile.NamedTemporaryFile(mode="w+", dir=os.path.dirname(file))

    # Copy the content over to the new file and modify the first line.
    for i, line in enumerate(all_file_lines):
        if i == 0:
            new_first_line = SPECIAL_FIRST_LINE + target_dir + "\n"
            temp.write(new_first_line)
        else:
            temp.write(line)

    # This temporary file is going to be used for a future filebench command.
    # As such, it's necessary to make sure that it is not buffered in any way. 
    temp.flush()
    os.sync()

    return temp



# Run the filebench command synchronously. This may take a long time.
def run_filebench_command(test: str, stats_dir: str, modified_glibc: str=None) -> None:

    stats_file_name = os.path.basename(test) + "_" + str(time.time())
    stats_file_path = os.path.join(stats_dir, stats_file_name)
    stats_file = open(stats_file_path, "x")

    print("Starting test " + test + "\n")
    print("Writing the results of this test to " + stats_file_path + "\n")
    subprocess.run(["filebench", "-f", test], stdout=stats_file, check=True)
    print("Finished test " + test + "\n")

    return



# Run a single filebench test. 
# 
# Notes:
#    This function does a number of things which impact the filesystem. It mounts
#       stuff, runs executables which create files, etc. When this function finishes
#       running, its net effect should be a single file written to the statistics
#       directory.
#
# Arguments:
#    test                     - String.
#                               Absolute path to a .f file.
#    stats_dir                - String.
#                               Absolute path to the directory where the statistics produced by
#                                  the filebench test will be dumped.
#    backing_store            - String.
#                               Absolute path to a file or disk partition which will be used
#                                 as the storage medium. This will be erased and reformatted
#                                 before every test.
#    backing_store_mountpoint - String.
#                               Absolute path to the desired mountpoint of the
#                                  backing store. The backing store will be mounted
#                                  here.
#    use_userspace_fs         - Boolean.
#                               Should the userspace filesystem be used? If the userspace
#                                  filesystem is not used, then the filebench workload will
#                                  be run on the backing store.
#
# Optional Arguments:
#    userspace_fs_mountpoint  - String.
#                               Absolute path of desired mountpoint of the
#                                  userspace filesystem. The userspace filesystem
#                                  will be mounted to this location.
#    userspace_fs_binary      - String.
#                               Absolute path to the executable which runs the userspace
#                                  filesystem daemon.
#    userspace_fs_opt         - Boolean.
#                               Should the optimized version of the userspace filesystem
#                                  daemon be used? (This may not be useful for general userspace
#                                  filesystems, but sure is relevant for StackFS)
#    modified_glibc           - String.
#                               Absolute path to a .so file representing a modified glibc.
#                                  If this is passed, then the filebench executable will be
#                                  linked against this modifed glibc.
# 
# Returns:
#    None. 
def run_test(test: str, stats_dir: str, backing_store: str, backing_store_mountpoint: str, 
             use_userspace_fs: bool, userspace_fs_mountpoint: str=None, userspace_fs_binary: str=None, 
             userspace_fs_opt: bool=False, modified_glibc: str=None) -> None: 

    # Reformat the underlying storage medium and mount it.
    reformat_backing_store(backing_store)
    mount_fs(backing_store_mountpoint, backing_store)

    if use_userspace_fs:
        # If userspace_fs is being used, start the daemon, mount the userspace
        #    filesystem, and point the Filebench workload at the mountpoint for
        #    the userspace filesystem.
        popen = start_userspace_fs(userspace_fs_binary, backing_store_mountpoint, userspace_fs_mountpoint, userspace_fs_opt)
        temp = set_filebench_target_dir(test, userspace_fs_mountpoint)
    else:
        # If userspace_fs is not being used, the filebench workload will operate on the
        #    in-kernel filesystem mounted at the backing store mountpoint.
        temp = set_filebench_target_dir(test, backing_store_mountpoint)

    prepare_for_test()

    run_filebench_command(temp.name, stats_dir, modified_glibc)

    if use_userspace_fs:
        teardown_userspace_fs(popen, userspace_fs_mountpoint)
    
    unmount_fs(backing_store_mountpoint)

    return



# Wrapper function for running consecutive tests.
def run_tests(tests: list[str], stats_dir: str, backing_store: str, backing_store_mountpoint: str, 
              use_userspace_fs: bool, userspace_fs_mountpoint: str=None, userspace_fs_binary: str=None, 
              userspace_fs_opt: bool=False, modified_glibc: str=None) -> None: 

    for test in tests:
        run_test(test, stats_dir, backing_store, backing_store_mountpoint, 
                 use_userspace_fs, userspace_fs_mountpoint, userspace_fs_binary, 
                 userspace_fs_opt, modified_glibc)



if __name__ == "__main__":

    # Parse and sanity check the passed arguments. 
    parser = build_argparser()
    args = vars(parser.parse_args())
    sanity_check_args(args)

    # The user can specify a single filebench test or a category of filebench tests.
    if args["filebench_test"]:
        tests = [args["filebench_test"]]
    else:
        workloads = determine_workloads()
        tests = workloads[args["filebench_category"]]

    # Run all the workloads.
    run_tests(tests, args["stats_dir"], args["backing_store"], 
              args["backing_store_mountpoint"], args["use_userspace_fs"], 
              args["userspace_fs_mountpoint"], args["userspace_fs_binary"],
              args["userspace_fs_opt"], args["modified_glibc"])