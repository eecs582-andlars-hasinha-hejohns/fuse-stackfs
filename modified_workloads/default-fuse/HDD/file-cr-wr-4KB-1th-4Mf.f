set mode quit alldone
set $dir=/home/andrew/userspace_mountpoint
set $nfiles=4000000
set $meandirwidth=1000
set $nthreads=1

define fileset name=bigfileset, path=$dir, entries=$nfiles, dirgamma=0, dirwidth=$meandirwidth, size=4k
define process name=fileopen, instances=1
{
        thread name=fileopener, memsize=4k, instances=$nthreads
        {
                flowop createfile name=create1, filesetname=bigfileset
                flowop writewholefile name=write-file, filesetname=bigfileset
                flowop closefile name=close-file,filesetname=bigfileset
        }
}

create files

# system "sync"
# system "echo 3 > /proc/sys/vm/drop_caches"

system "/home/andrew/fuse-stackfs/StackFS_LowLevel/StackFS_ll -s --statsdir=/tmp/ -r /home/andrew/underlying_filesystem/ext4_fs/ /home/andrew/userspace_mountpoint/ > /dev/null &"

system "echo started >> cpustats.txt"
system "echo started >> diskstats.txt"

run 60
