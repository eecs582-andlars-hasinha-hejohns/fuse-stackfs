set $dir=

set mode quit alldone
set $nthreads=1

define file name=bigfile, path=$dir, size=60g

define process name=fileopen, instances=1
{
    thread name=fileopener, memsize=128k, instances=$nthreads
    {
        flowop createfile name=create1, filesetname=bigfile
        flowop write name=write-file, filesetname=bigfile, iosize=128k,iters=491520
        flowop closefile name=close1
        flowop finishoncount name=finish, value=1, target=close1
    }
}

psrun 10