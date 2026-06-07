pkill -9 runsv
pkill -9 runsvdir
pkill Xtigervnc
pkill Xvnc
rm -f $PREFIX/tmp/.X1-lock
rm -rf /data/data/com.termux/files/usr/tmp/.X11-unix/*
rm -f /tmp/.X1-lock
rm -f /tmp/.X11-unix/X1
