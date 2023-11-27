#!/usr/bin/env bash

export PATH=$PATH:/home/andrew/libfuse/build/util/:/usr/sbin
sudo chown root:root ~/libfuse/build/util/fusermount3 
sudo chmod 4755 ~/libfuse/build/util/fusermount3