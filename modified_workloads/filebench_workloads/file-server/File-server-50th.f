set $dir=

set mode quit alldone
set $nfiles=200000
set $meandirwidth=20
set $nthreads=50
set $size1=128k

define fileset name=bigfileset, path=$dir, size=$size1, entries=$nfiles, dirwidth=$meandirwidth, prealloc

define process name=fileserver,instances=1
{
    thread name=fileserverthread, memsize=10m, instances=$nthreads
    {
        flowop createfile name=createfile1,filesetname=bigfileset,fd=1
        flowop writewholefile name=wrtfile1,srcfd=1,fd=1,iosize=1m
        flowop closefile name=closefile1,fd=1
        flowop openfile name=openfile1,filesetname=bigfileset,fd=1
        flowop appendfilerand name=appendfilerand1,iosize=16k,fd=1
        flowop closefile name=closefile2,fd=1
        flowop openfile name=openfile2,filesetname=bigfileset,fd=1
        flowop readwholefile name=readfile1,fd=1,iosize=1m
        flowop closefile name=closefile3,fd=1
        flowop deletefile name=deletefile1,filesetname=bigfileset
        flowop statfile name=statfile1,filesetname=bigfileset
        flowop finishoncount name=finish, value=1000000
    }
}

run