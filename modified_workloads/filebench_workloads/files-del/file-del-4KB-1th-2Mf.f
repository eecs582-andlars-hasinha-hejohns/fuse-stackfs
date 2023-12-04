set $dir=

set mode quit alldone
set $nfiles=2000000
set $meandirwidth=1000
set $nthreads=1

define fileset name=bigfileset, path=$dir, entries=$nfiles, dirwidth=$meandirwidth, dirgamma=0, size=4k, prealloc

define process name=fileopen, instances=1
{
    thread name=fileopener, memsize=4k, instances=$nthreads
    {
        flowop deletefile name=delete-file, filesetname=bigfileset
    }
}

run