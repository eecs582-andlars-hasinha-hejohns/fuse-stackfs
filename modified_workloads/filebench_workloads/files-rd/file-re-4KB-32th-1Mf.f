set $dir=

set mode quit alldone
set $nfiles=1000000
set $meandirwidth=1000
set $nthreads=32

define fileset name=bigfileset, path=$dir, entries=$nfiles, dirwidth=$meandirwidth, dirgamma=0, size=4k, prealloc

define process name=fileopen, instances=1
{
    thread name=fileopener, memsize=4k, instances=$nthreads
    {
        flowop openfile name=open1, filesetname=bigfileset, fd=1
        flowop readwholefile name=read-file, filesetname=bigfileset, iosize=4k, fd=1
        flowop closefile name=close-file, filesetname=bigfileset, fd=1
        flowop finishoncount name=finish, value=1200000
    }
}

run