set $dir=

set mode quit alldone
set $nfiles=1
set $nthreads=1
set $memsize=4k
set $iterations=262144

define file name=bigfileset, path=$dir, size=60g, prealloc

define process name=fileopen, instances=1
{
    thread name=fileopener, memsize=$memsize, instances=$nthreads
    {
        flowop openfile name=open1, filesetname=bigfileset, fd=1
        flowop read name=read-file, filesetname=bigfileset, random, iosize=$memsize, iters=$iterations, fd=1
        flowop closefile name=close1, fd=1
        flowop finishoncount name=finish, value=1
    }
}

run