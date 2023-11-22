This directory contains a script, `filebench_runner.py`, and some filebench workloads,
in `/filebench_workloads/`, which should make running all or a subset of the
filebench tests easy.

## How to use `filebench_runner.py` ##
1. The `filebench_runner.py` script must be invoked with superuser privileges because
it does things that only the superuser can do: mount filesystems, etc.
2. Use `python3 filebench_runner.py -h` to see a list of all available options. 

## Tips ##
If the `filebench_runner.py` script breaks while executing, it's possible that 
you will need to unmount some directories before re-running the `filebench_runner.py` 
script. If the `filebench_runner.py` does not break while executing, you don't need
to do anything.

If the `filebench_runner.py` script breaks and you need to unmount directories:
1. Run `mount -l` to see the list of all mounted directores on the system. If you
notice that the backing store is mounted or the userspace filesystem is mounted,
you'll need to unmount them manually.
2. To unmount the backing store manually, use `sudo umount /path/to/backing/store/mountpoint`.
3. To unmount the userspace file system manually, use `sudo fusermount3 /path/to/userspace/fs/mountpoint`.

The `filebench_runner.py` script assumes that `fusermount3` and `mke2fs` programs
live on the `PATH` of the superuser. Beware that on many systems, for security reasons,
the `PATH` for the superuser differs from that of other users. If this is the case,
make sure that `fusermount3` and `mke2fs` are actually on the `PATH` of the superuser.

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
- Use temporary file instead of modifying workload file directly.

