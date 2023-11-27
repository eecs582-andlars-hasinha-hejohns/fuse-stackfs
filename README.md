## Sources ##

Code:
- https://github.com/sbu-fsl/fuse-stackfs/tree/master
- https://github.com/libfuse/libfuse

Documentation:
- https://www.usenix.org/system/files/conference/fast17/fast17-vangoor.pdf
- https://www.fsl.cs.sunysb.edu/docs/fuse/fuse-tos19-a15-vangoor.pdf
- https://www.fsl.cs.stonybrook.edu/docs/fuse/fuse-article-appendices.html
- https://www.filesystems.org/fuse/
- https://github.com/libfuse/libfuse/releases
- https://www.cs.nmsu.edu/~pfeiffer/fuse-tutorial/html/index.html
- https://www.cs.hmc.edu/~geoff/classes/hmc.cs135.201109/homework/fuse/fuse_doc.html


## Stacked Filesystem History ##

The devs of StackFS didn't explicitly document what version of the Libfuse low
level API their filesystem is designed to be compatible with. However, they defined
the macro `FUSE_USE_VERSION` to be 30. Peering into the Libfuse library (see 
`include/fuse.h`, `include/fuse_common.h` for examples), we see that this macro
affects the interface of certain functions that it expects to be defined. It 
looks like we should change `FUSE_USE_VERSION` to be 316.

See https://www.fsl.cs.sunysb.edu/docs/fuse/fuse-tos19-a15-vangoor.pdf for the long
form version of the FUSE or Not to FUSE paper. In this report, they say that they
use libfuse commit #386b1b.

They also add instrumentation mechanisms to the libfuse library itself. These
mechanisms are referenced in the StackFS implementation, so they must also be
brought over to the newer version of libfuse.


## System Details ##

We want the stacked filesystem to run on a newer version of the Linux Kernel so
that we get access to the new io_uring mechanisms. The stacked filesystem talks 
directly to the Libfuse user space library, so we need to make sure that the 
stacked filesystem, the Libfuse library, and the Linux Kernel coexist correctly.

System:
- Debian v12.2
- Linux Kernel v6.1.0-13-amd64

The packages included with the Debian v12.2 ('bookworm') package management system are:
- Libfuse v3.14.0-4, the shared library ("apt install libfuse3-3")
- Fuse3 v3.14.0-4, fuse command line stuff ("apt install fuse3")
- Libfuse3-dev v3.14.0-4, files for development ("apt install libfuse3-dev")

However, we need customized versions of all of these components. See `Using Customized Libfuse`
below for instructions on how to get our customized versions. *You don't need to
install any of the libfuse functionality via apt, we will use a customized version
of libfuse, and all the associated tools, instead.*

Note: 
Even though Libfuse, Fuse3, and Libfuse3-dev all come as separate installs
via the package manager, the source files for all three are included in the libfuse
repo (https://github.com/libfuse/libfuse/tree/fuse-3.14.0).


## Using Customized Libfuse ##

1. We want the most up to date version of libfuse and we want libfuse to
be instrumented in the way that StackFS expects it to be. Clone https://github.com/eecs582-andlars-hasinha-hejohns/libfuse
and checkout the `with_instrumentation` branch.
2. We'll now build libfuse as a shared object file so that it can be linked to
create a StackFS binary executable. To do this, follow the build instructions which
accompany the customized version of libfuse. At the time of writing this, you should
do:

   ```
   mkdir build 
   cd build
   meson setup .. 
   ninja
   ```

   There is no need to run the tests which accompany the libfuse repo.
3. Check that the `build/` directory you just created contains `/lib/libfuse3.so`.
4. The StackFS binary executable needs access to the `fusermount3` executable. The
`fusermount3` executable should be located at `build/util/fusermount3`. Add the
`build/util` directory to `$PATH`. Furthermore, the `fusermount3` executable needs
to run as root since it is does a `mount`. To make it run as root and allow other
users to execute it, use: 

   ```
   sudo chown root:root ~/libfuse/build/util/fusermount3
   sudo chmod 4755 ~/libfuse/build/util/fusermount3
   ```

   All of this can be bundled into a shell script. See `setup.sh` for an example.


## Building and Running the Stacked Filesystem ##

Building:
1. Clone https://github.com/eecs582-andlars-hasinha-hejohns/fuse-stackfs and checkout
the `updating` branch.
2. Build the StackFS binary by doing `make` in the `StackFS_LowLevel`
directory. If you want an executable binary with debug symbols, use `make Debug`.
**Right now, there are some hardcoded paths in the makefile. Modify these if necessary.** 
3. Checkout the help options for the stacked filesystem binary via `./StackFS_ll -h`.

How To Use:
1. The stacked filesystem uses an underlying filesystem, such as ext4. For now, we
will not partition the backing store of the machine and create an ext4 filesystem
on the partition (i.e. directly on a block device). Instead, we'll create a 
filesystem within a file, mount the filesystem somewhere, and use it as the underlying 
filesystem. 

   To do this:
   ```
   touch ~/fs/ext4_fs
   mke2fs -t ext4 ~/fs/ext4_fs 2048
   sudo mount -t ext4 ~/fs/ext4_fs ~/fs/mountpoint
   sudo chmod -R 777 ~/fs/mountpoint/
   ```

   When you're done, clean up with:
   ```
   sudo umount ~/fs/mountpoint
   rmdir ~/fs/mountpoint
   rm ~/fs/ext4_fs
   ```

2. Now build the stacked filesystem binary and run the filesystem daemon.

   To run the filesystem daemon with a single thread and in foreground mode, use: 

   `./StackFS_ll -r ~/fs/mountpoint ~/userspace_mountpoint -s -f`


   To use the logging capability:

   `./StackFS_ll -r ~/fs/mountpoint ~/userspace_mountpoint -s -f --statsdir=/path/to/statsdir`

   When the executable receives a signal to dump the statistics it collected, it will
   dump the information to a file created in the `statsdir`. However, the executable
   only dumps this information when it receives a `SIGUSR1` signal. See the Collecting
   Runtime Statistics section below for more information.


   To do debugging:

   `gdb --args ./StackFS_ll -r ~/underlying_filesystem/mountpoint ~/userspace_mountpoint -s -f --statsdir=/path/to/statsdir`


   To do tracing:

   `./StackFS_ll -r ~/underlying_filesystem/mountpoint ~/userspace_mountpoint -s -f --statsdir=/path/to/statsdir --tracing`

   Unlike logging, tracing is more invasive. It heavily impacts the performance 
   of StackFS. When tracing is enabled and the StackFS receives a request
   from the kernel/library, it will record that it receieved the request. The requests
   get recorded in a file called `trace_stackfs.log` which is created in the
   `statsdir` directory. 

   When run in foreground mode, the executable will not return. Use `Ctrl+C` to kill the daemon. 

   **Once you have killed the daemon, it's necessary to run `fusermount3 -u ~/userspace_mountpoint` 
   to unmount the userspace filesystem. Doing this will only unmount the file system, the
   content of the file system will stil be intact.**

3. You can interact with the userspace filesystem normally:
   ```
   touch ~/userspace_mountpoint hello.txt
   echo "hello" > ~/userspace_mountpoint/hello.txt
   rm ~/userspace_mountpoint/hello.txt
   mkdir ~/userspace_mountpoint/test_dir
   ...
   ```
   **For security reasons, the userspace filesystem is only accessible to the user 
   who mounted the userspace filesystem. If you mount a userspace filesystem as 
   root, you must be root to access any information about it. This applies even
   if the directory in which the userspace filesystem lives was created by some
   other user. For example, user `andrew` might create a directory `~/userspace_mountpoint`
   and then user `root` might mount a userspace filesystem to this directory. If
   user `andrew` then attempts to issue `ls ~/userspace_mountpoint`, they will
   get a `Permission denied` error. Use `mount -l` to check which user mounted a 
   userspace filesystem.**


## Collecting Runtime Statistics ##

As the user interacts with the filesystem governed by StackFS, StackFS records
statistics about its performance. It will dump these statistics to a file when
it receives a `SIGUSR1` signal. It always dumps the statistics to `user_stats.txt`,
which is created in the `statsdir` passed to the executable.

After interacting with the filesystem, you can get statistics about its performance
by doing `kill -s SIGUSR1 <pid>`. This will cause the `user_stats.txt` file to
be created (or overwritten, if it already existed) and the statistics to be dumped
to this file.

When you look at `user_stats.txt`, it will contain a big grid of numbers:
```
0 0 0 0 0 0 0 0 0 0 7 11 6 7 16 1 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 
0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 
0 0 0 0 0 0 0 0 0 0 0 4 8 4 3 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 
0 0 0 0 0 0 0 0 0 0 0 0 0 2 0 1 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 
0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 
0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 
0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 
0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 
0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 2 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 
0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 
0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 
0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 
0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 
0 0 0 0 0 0 0 0 0 0 0 0 1 1 4 0 1 1 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 
0 0 0 0 0 0 0 0 0 0 0 0 1 1 1 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 
0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 2 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 
0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 
0 0 0 0 0 0 0 0 0 0 0 3 1 6 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 
0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 
0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 1 1 0 0 0 0 0 0 0 0 0 
0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 
0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 
0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 
0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 
0 0 0 0 1 4 1 7 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 
0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 
0 0 0 0 0 0 0 0 0 0 0 0 0 0 3 0 1 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 
0 0 0 0 0 0 0 0 0 0 0 1 3 0 1 1 2 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 
0 0 0 0 0 0 0 0 0 0 0 0 1 2 0 1 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 
0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 
0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 
0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 
0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 
0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 
0 0 0 0 0 0 0 0 0 0 0 0 0 0 1 0 0 1 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 
0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 
0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 
0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 
0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 
0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 
0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 
0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 
0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 
0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 
0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 
```
Each row in the grid corresponds to a particular operation passed from the kernel
to the stacked filesystem. For example, when the user creates a directory in the
userspace filesystem, a `FUSE_MKDIR` operation is passed to the StackFS daemon
and the daemon processes it. See `fuse_opcode` in `fuse_kernel.h` for a list of
all the opcodes that can be passed to the daemon. Note that the standard opcodes 
in `fuse_kernel.h` are integers in the range `[1, 51]`. As such, the first row in
the table correpsonds to `FUSE_LOOKUP`, the second row corresponds to `FUSE_FORGET`,
etc.

Each column in the grid corresponds to a time bucket. There are 33 columns (assume
they are labeled `[0, 32]`) and the time bucket for column with label `i` is 
$[0 \text{ ns}, 1 \text{ ns}]$ when $i = 0$ and $[2^i \text{ ns}, 2^{i+1} - 1 \text{ ns}]$
when $i > 0$. The second to last bucket corresponds to, approximately, $[4.2 \text{ s}, 8.6 \text{ s}]$. If
the runtime exceeds $2^{33} \text{ ns} = 8.6 \text{ s}$, then it falls into the catch all last 
bucket.

## The `/sys/fs/fuse/connections/` Directory ##
The `/sys/fs/fuse/connections/` directory contains one directory for each mounted 
userspace filesystem. The directory names are minor device numbers (use `stat` 
to view the device number of a mounted userspace filesystem). Each subdirectory 
contains 4 files which contain information about the FUSE queues in the kernel. It's
not clear to me what the significance of the `congestion_threshold` file is.


## Running the Filebench Performance Tests ##
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

2.  




## TODO ##
- Upgrade to Linux 6.6 kernel.
- Add error handling to main() in StackFS_LowLevel.c.
- Comment out all the tracing when doing measurements!
- Enable all the time keeping in libfuse (which is in addition to the time keeping the StackFS itself)? See the calls to clock_gettime().

## Odd Things Noticed in *To FUSE or Not to FUSE: Performance of User-Space File Systems* ##
- In the file create workloads, they not only create the files but do write their
entire content!

## Possible Extensions **
- Consider aiowrite/aiowait flowops for additional filebench experiments.
- Could we run tests with a different user space file system?