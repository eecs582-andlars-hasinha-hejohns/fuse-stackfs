## Stacked Filesystem History ##

The devs of StackFS didn't explicitly document what version of the Libfuse low
level API their filesystem is designed to be compatible with. However, they defined
the macro FUSE_USE_VERSION to be 30. Peering into the Libfuse library (see 
`include/fuse.h`, `include/fuse_common.h` for examples), we see that this macro
affects the interface of certain functions that it expects to be defined. It 
looks like we should change FUSE_USE_VERSION to be 35 (even though we are using 
v3.14.0 of the library, it's not clear what the mapping between the 
FUSE_USE_VERSION and the tagged versioning system is).

Note: 
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

TODO:
- Need to study the logging mechanisms in the stacked filesystem. I have commented
out the fuse_session_add_statsDir() stuff to get things building for now.
- Need to figure out what the generate_time(), populate_time(), etc. are doing.
- Need to figure out what the "rootDir" is and why it must be passed as an argument
to the user space file implementation binary.

How To Use:
1. 