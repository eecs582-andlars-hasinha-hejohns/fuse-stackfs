This directory contains a script, `filebench_runner.py`, and some filebench workloads,
in `/filebench_workloads/`, which should make running all or a subset of the
filebench tests easy.

The filebench workloads only contain minimal workload specification. In particular,
the filebench workloads **don't** do things like setup a userspace filesystem,
tear down old userspace filesystems, clear caches, etc. All of these auxiliary actions
are the responsibility of the `filebench_runner.py` script.

## How to use `filebench_runner.py` ##

