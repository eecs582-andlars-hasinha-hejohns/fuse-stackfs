set $dir=

set mode quit alldone
set $nthreads=1

define file name=bigfile, path=$dir, size=60g

define process name=fileopen, instances=1
{
    thread name=fileopener, memsize=1m, instances=$nthreads
    {
        flowop createfile name=create1, filesetname=bigfile
        flowop write name=write-file, filesetname=bigfile, iosize=1m,iters=61440
        flowop closefile name=close1
        flowop finishoncount name=finish, value=1
    }
}

run