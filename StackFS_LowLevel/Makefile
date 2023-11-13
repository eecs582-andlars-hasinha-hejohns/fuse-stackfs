all: StackFS_ll

StackFS_ll:
	# gcc -Wall -Werror StackFS_LowLevel.c `pkg-config fuse3 --cflags --libs` -o StackFS_ll

	# Don't use the system libfuse.
	gcc -Wall -Werror -L/home/andrew/libfuse/build/lib/ -lpthread -I/home/andrew/libfuse/include/ StackFS_LowLevel.c -lfuse3 -o StackFS_ll

clean:
	rm -rf StackFS_ll
