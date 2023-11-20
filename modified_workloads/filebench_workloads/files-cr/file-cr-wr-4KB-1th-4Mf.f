set $dir=

set mode quit alldone
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
        flowop closefile name=close-file, filesetname=bigfileset
    }
}

run 