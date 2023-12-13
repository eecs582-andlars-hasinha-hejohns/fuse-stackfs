#!/usr/bin/env bash

# Modified glibc, StackFS
sudo -E bash -c "python3 filebench_runner.py /dev/vda3 /home/andrew/test_dir /home/andrew/stats_dir_4_vcpus_final/customglibc_stackfs --custom_tests1 --use_userspace_fs --userspace_fs_mountpoint /home/andrew/userspace_mountpoint --userspace_fs_binary /home/andrew/fuse-stackfs/StackFS_LowLevel/StackFS_ll --modified_glibc /home/andrew/io_uring_example/libmonkey/libmonkey.so"

# System glibc, StackFS
sudo -E bash -c "python3 filebench_runner.py /dev/vda3 /home/andrew/test_dir /home/andrew/stats_dir_4_vcpus_new/sysglibc_stackfs --custom_tests1 --use_userspace_fs --userspace_fs_mountpoint /home/andrew/userspace_mountpoint --userspace_fs_binary /home/andrew/fuse-stackfs/StackFS_LowLevel/StackFS_ll"

# System glibc, kernel fs
sudo -E bash -c "python3 filebench_runner.py /dev/vda3 /home/andrew/test_dir /home/andrew/stats_dir_4_vcpus_new/sysglibc_kernelfs --custom_tests1"

# Modified glibc, kernel fs
sudo -E bash -c "python3 filebench_runner.py /dev/vda3 /home/andrew/test_dir /home/andrew/stats_dir_4_vcpus_new/customglibc_kernelfs --custom_tests1 --modified_glibc /home/andrew/io_uring_example/libmonkey/libmonkey.so"
