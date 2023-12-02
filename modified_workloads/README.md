This directory contains a script, `filebench_runner.py`, and some filebench workloads,
in `/filebench_workloads/`, which should make running all or a subset of the
filebench tests easy.

## Setting up Filebench ##

1. Build Filebench 1.5-alpha3 from source (https://github.com/filebench/filebench) and install
it using the steps detailed in the repo. Before building and installing, modify
`FILEBENCH_NFILESETENTRIES` in `ipc.h` to be `1024 * 1024 * 10`. By default, filebench
hardcodes the maximum number of files which can be created to be `1024 * 1024`.
The largest test we run creates 4 million files, so this hardcoded maximum must be
increased.

   **Warning: There is currently a bug in the Filebench implementation such that, for
   (relatively) new versions of the Linux kernel it is necessary to turn off virtual
   address space randomization. See https://github.com/filebench/filebench/issues/156.
   The upshot is that it's necessary to turn off virtual address space randomization
   via `sudo bash -c "echo 0 > /proc/sys/kernel/randomize_va_space"` before running
   any filebench test.**

## How to use `filebench_runner.py` ##
1. The `filebench_runner.py` script must be invoked with superuser privileges because
it does things that only the superuser can do: mount filesystems, etc.
2. Use `python3 filebench_runner.py -h` to see a list of all available options. 

## Tips ##
If the `filebench_runner.py` script breaks while executing, it's possible that 
you will need to unmount some directories before re-running the `filebench_runner.py` 
script. If the `filebench_runner.py` does not break while executing, you don't need
to do anything.

### What to do if `filebench_runner.py` breaks. ###
If the `filebench_runner.py` script breaks and you need to unmount directories:
1. Run `mount -l` to see the list of all mounted directores on the system. If you
notice that the backing store is mounted or the userspace filesystem is mounted,
you'll need to unmount them manually.
2. To unmount the backing store manually, use `sudo umount /path/to/backing/store/mountpoint`.
3. To unmount the userspace file system manually, use `sudo fusermount3 /path/to/userspace/fs/mountpoint`.

### Assumptions that `filebench_runner.py` makes. ###
The `filebench_runner.py` script assumes that `fusermount3` and `mke2fs` programs
live on the `PATH` of the superuser. Beware that on many systems, for security reasons,
the `PATH` for the superuser differs from that of other users. If this is the case,
make sure that `fusermount3` and `mke2fs` are actually on the `PATH` of the superuser.

### Filesystem Sizes ###
The `filebench_runner.py` script hardcodes the size of the underlying filesystem. If you try to run a filebench test which uses a very large amount of memory (some tests use up to `60 GB`) and either the backing store runs out of space or the underlying filesystem runs out of space, you should anticipate seeing an error which says something like "Could not allocate file with name /bigfileset/0000001 ....".

## Running Filebench Workloads Directly ## 
The filebench workloads only contain minimal workload specification. In particular,
the filebench workloads **don't** do things like setup a userspace filesystem,
tear down old userspace filesystems, clear caches, etc. All of these auxiliary actions
are the responsibility of the `filebench_runner.py` script.

Note that running the filebench workloads directly, instead of using the `filebench_runner.py`
script, will not work in general. This is because the `dir` variable is not defined
in any of workload scripts. Notice that each script begins with the line `set $dir=`.
The target directory of each workload is set at runtime of the `filebench_runner.py` script.
If you want to run a filebench workload directly, fill in the `set $dir` line.

## TODO ##
- Add the same optimization capability as the *To FUSE or Not to FUSE* paper. 
