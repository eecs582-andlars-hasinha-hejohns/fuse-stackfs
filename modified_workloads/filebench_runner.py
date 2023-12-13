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



# Assumptions about name of directory containing the filebench workloads and the
#    relative path of the workload directory with respect to this file.
FILEBENCH_WORKLOAD_DIR_NAME = "filebench_workloads"
filebench_workload_dir_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), FILEBENCH_WORKLOAD_DIR_NAME)

CUSTOM_TEST_LIST0 = ["/home/andrew/fuse-stackfs/modified_workloads/filebench_workloads/file-server/File-server-50th.f",
                     "/home/andrew/fuse-stackfs/modified_workloads/filebench_workloads/files-cr/file-cr-wr-4KB-1th-4Mf.f",
                     "/home/andrew/fuse-stackfs/modified_workloads/filebench_workloads/files-rd/file-re-4KB-1th-1Mf.f",
                     "/home/andrew/fuse-stackfs/modified_workloads/filebench_workloads/mail-server/Mail-server-16th.f",
                     "/home/andrew/fuse-stackfs/modified_workloads/filebench_workloads/web-server/Web-server-100th.f",
                     "/home/andrew/fuse-stackfs/modified_workloads/filebench_workloads/rnd-rd-1th-1f/file-rd-re-1MB-1th-1f.f",
                     "/home/andrew/fuse-stackfs/modified_workloads/filebench_workloads/rnd-rd-1th-1f/file-rd-re-4KB-1th-1f.f",
                     "/home/andrew/fuse-stackfs/modified_workloads/filebench_workloads/rnd-rd-32th-1f/file-rd-re-1MB-32th-1f.f",
                     "/home/andrew/fuse-stackfs/modified_workloads/filebench_workloads/rnd-rd-32th-1f/file-rd-re-4KB-32th-1f.f",
                     "/home/andrew/fuse-stackfs/modified_workloads/filebench_workloads/rnd-wr-1th-1f/file-rd-wr-1MB-1th-1f.f",
                     "/home/andrew/fuse-stackfs/modified_workloads/filebench_workloads/rnd-wr-1th-1f/file-rd-wr-4KB-1th-1f.f",
                     "/home/andrew/fuse-stackfs/modified_workloads/filebench_workloads/rnd-wr-32th-1f/file-rd-wr-1MB-32th-1f.f",
                     "/home/andrew/fuse-stackfs/modified_workloads/filebench_workloads/rnd-wr-32th-1f/file-rd-wr-4KB-32th-1f.f",
                     "/home/andrew/fuse-stackfs/modified_workloads/filebench_workloads/seq-rd-1th-1f/file-sq-re-1MB-1th-1f.f",
                     "/home/andrew/fuse-stackfs/modified_workloads/filebench_workloads/seq-rd-1th-1f/file-sq-re-4KB-1th-1f.f",
                     "/home/andrew/fuse-stackfs/modified_workloads/filebench_workloads/seq-rd-32th-1f/file-sq-re-1MB-32th-1f.f",
                     "/home/andrew/fuse-stackfs/modified_workloads/filebench_workloads/seq-rd-32th-1f/file-sq-re-4KB-32th-1f.f",
                     "/home/andrew/fuse-stackfs/modified_workloads/filebench_workloads/seq-rd-32th-32f/file-sq-re-1MB-32th-32f.f",
                     "/home/andrew/fuse-stackfs/modified_workloads/filebench_workloads/seq-rd-32th-32f/file-sq-re-4KB-32th-32f.f",
                     "/home/andrew/fuse-stackfs/modified_workloads/filebench_workloads/seq-wr-1th-1f/file-sq-wr-1MB-1th-1f.f",
                     "/home/andrew/fuse-stackfs/modified_workloads/filebench_workloads/seq-wr-1th-1f/file-sq-wr-4KB-1th-1f.f",
                     "/home/andrew/fuse-stackfs/modified_workloads/filebench_workloads/seq-wr-32th-32f/file-sq-wr-1MB-32th-32f.f",
                     "/home/andrew/fuse-stackfs/modified_workloads/filebench_workloads/seq-wr-32th-32f/file-sq-wr-4KB-32th-32f.f",
                     "/home/andrew/fuse-stackfs/modified_workloads/filebench_workloads/files-del/file-del-4KB-1th-2Mf.f",
                    ] 

CUSTOM_TEST_LIST1 = ["/home/andrew/fuse-stackfs/modified_workloads/filebench_workloads/file-server/File-server-50th.f",
                     "/home/andrew/fuse-stackfs/modified_workloads/filebench_workloads/rnd-wr-1th-1f/file-rd-wr-1MB-1th-1f.f",
                     "/home/andrew/fuse-stackfs/modified_workloads/filebench_workloads/seq-wr-1th-1f/file-sq-wr-4KB-1th-1f.f",                   
                     "/home/andrew/fuse-stackfs/modified_workloads/filebench_workloads/rnd-rd-32th-1f/file-rd-re-4KB-32th-1f.f",
                     "/home/andrew/fuse-stackfs/modified_workloads/filebench_workloads/mail-server/Mail-server-16th.f",
                     "/home/andrew/fuse-stackfs/modified_workloads/filebench_workloads/files-del/file-del-4KB-1th-2Mf.f",
                     "/home/andrew/fuse-stackfs/modified_workloads/filebench_workloads/seq-rd-32th-32f/file-sq-re-1MB-32th-32f.f"
                    ]


# Given a category name, this function returns an absolute path to the category.
def construct_category_path(filebench_category: str) -> str:

    return os.path.join(filebench_workload_dir_path, filebench_category)


# Returns a list containing absolute paths to all tests.
def find_all_workloads():

    all_tests = find_workloads(filebench_workload_dir_path)
    tests = []
    for category in all_tests:
        tests.extend(all_tests[category])
    return tests


# Uses the passed directory to determine the workload categories and workloads.
#    Assumes that the directory contains directories which name the workload
#    categories and the directories contain the workloads.
# The returned dictionary has keys which are absolute paths to dictionary categories
#    and values which are absolute paths to filebench workloads (.f files).
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
            workloads[root] = []
            for file in files:
                workloads[root].append(os.path.join(root, file))

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
                                 filebench tests to run. Should be unqualified name of a \
                                 subdirectory in the filebench_workloads directory.", 
                                 action='store')

    filebench_group.add_argument("--filebench_test", help="Path to .f file. A \
                                 particular filebench test to run.", action='store')
    
    filebench_group.add_argument("--all_tests", help="Flag indicating that the user wants \
                                  to run all filebench tests in all categories.", required=False,
                                  default=False, action='store_true')

    filebench_group.add_argument("--all_tests_from", help="Option to allow all tests after a particular \
                                  test to run. This is useful if, for example, one \
                                  test may have failed :( and you want to skip it.", required=False,
                                  action='store')

    filebench_group.add_argument("--custom_tests0", help="Option to run a custom set of hardcoded tests.",
                                 required=False, default=False, action='store_true')
    
    filebench_group.add_argument("--custom_tests1", help="Option to run a custom set of hardcoded tests.",
                                 required=False, default=False, action='store_true')

    parser.add_argument("--modified_glibc", help="Path to the .so file containing \
                        the modified glibc. This .so file does not need to contain a \
                        whole glibc, it can contain a subset of the glibc functionality \
                        that you wich to override. Linking is achieved with the LD_PRELOAD \
                        trick. If this argument is specified, the filebench \
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
        category_path = construct_category_path(args["filebench_category"])
        if not os.path.exists(category_path):
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
def reformat_backing_store(store: str, size: int=70000000) -> None:

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

    with open("/proc/sys/kernel/randomize_va_space", "r+") as outfile:
        if outfile.read(1) != "0":
            print("It was detected that you have virtual address space randomization turned on. This generally causes the Filebench executable to be non-functioning.")
            raise AssertionError("Please turn virtual address space randomization off!!!")

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
#
# Arguments:
#    test_name    - String.
#                   Absolute path to the filebench test to run. 
#    desired_name - String.
#                   The name of the filebench test. This could be different than
#                      the name of the filbench test file. Hint: When creating a
#                      temporary file, the name of the temporary file is odd and
#                      uninformative. 
#    stats_dir    - String.
#                   Absolute path to the statistics directory where the results
#                      of this filebench test will be dumped.
#
# Optional Arguments:
#    modified_glibc - String.
#                     Absolute path to the modified glibc shared object (.so) file
#                        which will be linked against the filebench executable.
#
# Return:
#    None.
def run_filebench_command(test_name: str, desired_name: str, stats_dir: str, modified_glibc: str=None) -> None:

    stats_file_name = os.path.basename(desired_name) + "_" + str(time.time())
    stats_file_path = os.path.join(stats_dir, stats_file_name)
    stats_file = open(stats_file_path, "x")

    print("Starting test " + desired_name + "\n")
    print("Writing the results of this test to " + stats_file_path + "\n")
    if modified_glibc is None:
        subprocess.run(["filebench", "-f", test_name], stdout=stats_file, check=True)
    else:
        os.putenv("LD_PRELOAD", modified_glibc)
        subprocess.run(["filebench", "-f", test_name], stdout=stats_file, check=True)
        os.unsetenv("LD_PRELOAD")
    print("Finished test " + desired_name + "\n")

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

    desired_name = os.path.basename(test)
    run_filebench_command(temp.name, desired_name, stats_dir, modified_glibc)

    if use_userspace_fs:
        teardown_userspace_fs(popen, userspace_fs_mountpoint)
    
    unmount_fs(backing_store_mountpoint)

    return



# Wrapper function for running consecutive tests.
def run_tests(tests: list[str], stats_dir: str, backing_store: str, backing_store_mountpoint: str, 
              use_userspace_fs: bool, userspace_fs_mountpoint: str=None, userspace_fs_binary: str=None, 
              userspace_fs_opt: bool=False, modified_glibc: str=None) -> None: 

    for i, test in enumerate(tests):

        print()
        print("*******************************************************************")
        print("Starting test " + str(i + 1) + " of " + str(len(tests)))
        print()

        run_test(test, stats_dir, backing_store, backing_store_mountpoint, 
                 use_userspace_fs, userspace_fs_mountpoint, userspace_fs_binary, 
                 userspace_fs_opt, modified_glibc)

        print("*******************************************************************")



if __name__ == "__main__":

    # Parse and sanity check the passed arguments. 
    parser = build_argparser()
    args = vars(parser.parse_args())
    sanity_check_args(args)

    # The user may want to run a single test, a category of test, or all the tests.
    if args["filebench_test"]:
        tests = [args["filebench_test"]]
    elif args["filebench_category"]:
        path_to_category = construct_category_path(args["filebench_category"]) 
        tests = find_workloads(filebench_workload_dir_path)[path_to_category]
    elif args["all_tests"]:
        tests = find_all_workloads()
    elif args["all_tests_from"]:
        tests = find_all_workloads()
        target_test = args["all_tests_from"]
        assert(target_test in tests)
        tests = tests[tests.index(target_test) + 1:] 
    elif args["custom_tests0"]:
        tests = CUSTOM_TEST_LIST0
    elif args["custom_tests1"]:
        tests = CUSTOM_TEST_LIST1
    else:
        raise AssertionError("Failure...")

    # Run all the workloads.
    run_tests(tests, args["stats_dir"], args["backing_store"], 
              args["backing_store_mountpoint"], args["use_userspace_fs"], 
              args["userspace_fs_mountpoint"], args["userspace_fs_binary"],
              args["userspace_fs_opt"], args["modified_glibc"])