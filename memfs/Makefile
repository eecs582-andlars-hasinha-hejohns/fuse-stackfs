all: memfs_ll

memfs_ll:
	# gcc -Wall -Werror memfs_lowlevel.c `pkg-config fuse3 --cflags --libs` -o memfs 

	# Don't use the system libfuse.
	gcc -Wall -Werror -L/home/andrew/libfuse/build/lib/ -lpthread -I/home/andrew/libfuse/include/ memfs_lowlevel.c -lfuse3 -o memfs 

clean:
	rm -rf memfs
