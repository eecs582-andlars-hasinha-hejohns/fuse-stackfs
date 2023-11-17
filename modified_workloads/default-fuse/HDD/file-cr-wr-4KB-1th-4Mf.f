set mode quit alldone
set $dir=/home/andrew/userspace_mountpoint
#Fixing I/O amount to be 4M files
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
#prealloc the file on EXT4 F/S (save the time)
system "mkdir -p /home/andrew/userspace_mountpoint/FUSE_EXT4_FS"
system "mkdir -p /home/andrew/userspace_mountpoint/EXT4_FS"

create files

#Move everything created under FUSE-EXT4 dir to EXT4 (Though nothing in this case)
system "mv /home/andrew/userspace_mountpoint/FUSE_EXT4_FS/* /home/andrew/userspace_mountpoint/EXT4_FS/"

system "sync"
system "echo 3 > /proc/sys/vm/drop_caches"

#mount FUSE FS (default) on top of EXT4
system "/home/andrew/fuse-stackfs/StackFS_LowLevel/StackFS_ll -r ~/underlying_filesystem/mountpoint ~/userspace_mountpoint -s -f --statsdir=/home/andrew/fuse-stackfs/StackFS_LowLevel/test_statsdir > /dev/null &`

system "echo started >> cpustats.txt"
system "echo started >> diskstats.txt"
psrun -10
