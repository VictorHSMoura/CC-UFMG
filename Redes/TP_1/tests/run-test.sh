#!/bin/bash
set -eu

N=$1

# Leave server window open during debug (close with C-b :kill-pane)
# tmux set-window-option remain-on-exit on
tmux split-pane -v -c $(pwd) ../servidor 51511
./client.py --script test$N-script.txt

K=1
while [[ -e test$N-output$K.txt ]] ; do
    if ! diff test$N-output$K.txt output$K.txt > /dev/null ; then
        echo "test$N failed"
        exit 1
    fi
    K=$(( K+1 ))
done

echo "test$N passed"
rm -rf client.log output*.txt
