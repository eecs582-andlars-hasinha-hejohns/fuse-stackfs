#!/usr/bin/env bash

# Modified glibc, StackFS
sudo -E bash -c "python3 filebench_runner.py /dev/vda3 /home/andrew/test_dir /home/andrew/test_statsdir --all_tests_from /home/andrew/fuse-stackfs/modified_workloads/filebench_workloads/web-server/Web-server-100th.f --use_userspace_fs --userspace_fs_mountpoint /home/andrew/userspace_mountpoint --userspace_fs_binary /home/andrew/fuse-stackfs/StackFS_LowLevel/StackFS_ll --modified_glibc /home/andrew/io_uring_example/test-monkey/test-monkey.so"

# System glibc, StackFS
sudo -E bash -c "python3 filebench_runner.py /dev/vda3 /home/andrew/test_dir /home/andrew/test_statsdir --all_tests --use_userspace_fs --userspace_fs_mountpoint /home/andrew/userspace_mountpoint --userspace_fs_binary /home/andrew/fuse-stackfs/StackFS_LowLevel/StackFS_ll"

# System glibc, kernel fs
sudo -E bash -c "python3 filebench_runner.py /dev/vda3 /home/andrew/test_dir /home/andrew/test_statsdir --all_tests"