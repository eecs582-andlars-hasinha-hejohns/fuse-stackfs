## Stacked Filesystem History ##

The devs of StackFS didn't explicitly document what version of the Libfuse low
level API their filesystem is designed to be compatible with. However, they defined
the macro FUSE_USE_VERSION to be 30. Peering into the Libfuse library (see 
`include/fuse.h`, `include/fuse_common.h` for examples), we see that this macro
affects the interface of certain functions (actually, only 1 function?!?) that 
it expects are defined. It appears as though changing FUSE_USE_VERSION to 314, 
corresponding to the newest version of Libfuse installed on our system, will
necessitate some changes being made.


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

Note: Even though Libfuse, Fuse3, and Libfuse3-dev all come as separate installs
via the package manager, the source files for all three are included in the libfuse
repo (https://github.com/libfuse/libfuse/tree/fuse-3.14.0).


## Building and Running the Stacked Filesystem ##

