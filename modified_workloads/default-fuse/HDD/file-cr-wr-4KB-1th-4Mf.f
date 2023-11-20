set mode quit alldone
set $dir=/home/andrew/filebench_test_mountpoint
set $nfiles=4000000
set $meandirwidth=1000
set $nthreads=1

define fileset name=bigfileset, path=$dir, entries=$nfiles, dirgamma=0, dirwidth=$meandirwidth, size=4k, prealloc

define process name=fileopen, instances=1
{
    thread name=fileopener, memsize=4k, instances=$nthreads
    {
        flowop createfile name=create1, filesetname=bigfileset
        flowop writewholefile name=write-file, filesetname=bigfileset
        flowop closefile name=close-file,filesetname=bigfileset
    }
}

system "/home/andrew/fuse-stackfs/StackFS_LowLevel/StackFS_ll -s --statsdir=/tmp/ -r /home/andrew/underlying_filesystem/mountpoint /home/andrew/userspace_mountpoint/ > /dev/null"
run 60
