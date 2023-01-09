#!/bin/sh
cd ~/Dev/busDevEmail/emailAutomation/

if ps -ef | grep -v grep | grep automateOutreach.py ; then
        :
else
        setsid python3 ./automateOutreach.py &
        :
fi

if [ "$(( $(date +"%s") - $(stat -c "%Y" "logFile.txt") ))" -gt "600" ]; then
        pkill -9 -f automateOutreach.py
        setsid python3 ./automateOutreach.py &
        :
fi
