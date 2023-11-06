## System Details ##

We want the stacked filesystem to run on a newer version of the Linux Kernel so
that we get access to the new io_uring mechanisms. The stacked filesystem talks 
directly to the Libfuse user space library, so we need to make sure that the 
stacked filesystem, the Libfuse library, and the Linux Kernel coexist correctly.

System:
- Debian v12.2
- Linux Kernel v6.1.0-13-amd64

Dependencies:
- Libfuse v3.14.0-4 ("apt install libfuse3-3")
- Fuse3 v3.14.0-4, Fuse command line stuff ("apt install fuse3")
- Libfuse3-dev v3.14.0-4, files for development ("apt install libfuse3-dev")

Note: Even though Libfuse, Fuse3, and Libfuse3-dev all come as separate installs
via the package manager, the source files for all three are included in the libfuse
repo (https://github.com/libfuse/libfuse/tree/fuse-3.14.0).



## Building and Running the Stacked Filesystem ##

