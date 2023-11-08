## Sources ##

Code: 
https://github.com/sbu-fsl/fuse-stackfs/tree/master
https://github.com/libfuse/libfuse

Documentation:
https://www.usenix.org/system/files/conference/fast17/fast17-vangoor.pdf
https://www.fsl.cs.sunysb.edu/docs/fuse/fuse-tos19-a15-vangoor.pdf
https://www.fsl.cs.stonybrook.edu/docs/fuse/fuse-article-appendices.html
https://www.filesystems.org/fuse/
https://github.com/libfuse/libfuse/releases
https://www.cs.nmsu.edu/~pfeiffer/fuse-tutorial/html/index.html
https://www.cs.hmc.edu/~geoff/classes/hmc.cs135.201109/homework/fuse/fuse_doc.html


## Stacked Filesystem History ##

The devs of StackFS didn't explicitly document what version of the Libfuse low
level API their filesystem is designed to be compatible with. However, they defined
the macro `FUSE_USE_VERSION` to be 30. Peering into the Libfuse library (see 
`include/fuse.h`, `include/fuse_common.h` for examples), we see that this macro
affects the interface of certain functions that it expects to be defined. It 
looks like we should change `FUSE_USE_VERSION` to be 314.

See https://www.fsl.cs.sunysb.edu/docs/fuse/fuse-tos19-a15-vangoor.pdf for the long
form version of the FUSE or Not to FUSE paper. In this report, they say that they
use libfuse commit #386b1b.


## System Details ##

We want the stacked filesystem to run on a newer version of the Linux Kernel so
that we get access to the new io_uring mechanisms. The stacked filesystem talks 
directly to the Libfuse user space library, so we need to make sure that the 
stacked filesystem, the Libfuse library, and the Linux Kernel coexist correctly.

System:
- Debian v12.2
- Linux Kernel v6.1.0-13-amd64

We need the stacked filesystem to be compatible with:
- Libfuse v3.14.0-4, the shared library ("apt install libfuse3-3")
- Fuse3 v3.14.0-4, fuse command line stuff ("apt install fuse3")
- Libfuse3-dev v3.14.0-4, files for development ("apt install libfuse3-dev")

Note: 
Even though Libfuse, Fuse3, and Libfuse3-dev all come as separate installs
via the package manager, the source files for all three are included in the libfuse
repo (https://github.com/libfuse/libfuse/tree/fuse-3.14.0).


## Building and Running the Stacked Filesystem ##

Notes:
- See the help options for the stacked filesystem binary via `./StackFS_ll -h`.

How To Use:
1. The stacked filesystem uses an underlying filesystem, such as ext4. For now, we
will not partition the backing store of the machine and create an ext4 filesystem
on the partition (i.e. directly on a block device). Instead, we'll create a 
filesystem within a file, mount the filesystem somewhere, and use it as the underlying 
filesystem. 

   To do this:
   1. Create the file for the filesystem: `touch ~/fs/ext4_fs`
   2. Format the file so it is an ext4 filesystem: `mke2fs -t ext4 ~/fs/ext4_fs 2048`
   3. Mount the filesystem at some mountpoint: `sudo mount -t ext4 ~/fs/ext4_fs ~/fs/mountpoint`
   4. Change the directory permissions: `sudo chmod -R 777 ~/fs/mountpoint/`

   When you're done, clean up with:
   ```
   sudo umount ~/fs/mountpoint
   rmdir ~/fs/mountpoint
   rm ~/fs/ext4_fs
   ```

2. Now build the stacked filesystem binary and run the filesystem daemon.

   To run the filesystem daemon with a single thread and in foreground mode, use: 
   `./StackFS_ll -r ~/fs/mountpoint ~/userspace_mountpoint -s -f`

   This command will not return. To kill it, send an interrupt signal via `Ctrl-C`.
   Right now this appears to cause a segfault in the signal handler, this may need
   to be fixed. 
   ** Once you have killed the daemon, it's necessary to run `fusermount3 -u ~/userspace_mountpoint` 
   to unmount the userspace file system. this will cause all the content of the 
   userspace filesystem to be erased. **

3. You can interact with the userspace filesystem normally:
   ```
   touch ~/userspace_mountpoint hello.txt
   echo "hello" > ~/userspace_mountpoint/hello.txt
   rm ~/userspace_mountpoint/hello.txt
   ```

4. ....TODO



## TODO ##

- Need to study the logging mechanisms in the stacked filesystem. I have commented
out the fuse_session_add_statsDir() stuff to get things building for now.

- Need to figure out what the generate_time(), populate_time(), etc. are doing.