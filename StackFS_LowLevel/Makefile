all: StackFS_ll

StackFS_ll:
	gcc -Wall -Werror -I/home/andrew/libfuse/include/ StackFS_LowLevel.c -o StackFS_ll -Wl,-L,/home/andrew/libfuse/build/lib/ -Wl,-l,pthread -Wl,-l,fuse3 -Wl,-rpath=/home/andrew/libfuse/build/lib/

Debug:
	gcc -ggdb -Og -Wall -Werror -I/home/andrew/libfuse/include/ StackFS_LowLevel.c -o StackFS_ll -Wl,-L,/home/andrew/libfuse/build/lib/ -Wl,-l,pthread -Wl,-l,fuse3 -Wl,-rpath=/home/andrew/libfuse/build/lib/

clean:
	rm -rf StackFS_ll
