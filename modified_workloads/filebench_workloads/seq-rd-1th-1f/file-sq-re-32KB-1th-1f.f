set $dir=

set mode quit alldone
set $nfiles=1
set $meandirwidth=1
set $nthreads=1

define fileset name=bigfileset, path=$dir, entries=$nfiles, dirwidth=$meandirwidth, size=60g, prealloc

define process name=fileopen, instances=1
{
    thread name=fileopener, memsize=32k, instances=$nthreads
    {
        flowop openfile name=open1, filesetname=bigfileset, fd=1
        flowop read name=read-file, filesetname=bigfileset, iosize=32k, iters=1966080, fd=1
        flowop closefile name=close1, fd=1
        flowop finishoncount name=finish, value=1
    }
}

run