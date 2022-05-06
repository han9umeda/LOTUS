#!/bin/sh

if [ $# != 2 ]; then
  echo "Usage: $0 [via AS Number] [target AS Number]" 1>&2
  exit 1
fi

expect -c "
set timeout -1
spawn python3 ../main.py
expect \"LOTUS >> \"
send \"import jpnic_network.yml\n\"
expect \"LOTUS >> \"
send \"run\n\"
expect \"LOTUS >> \"
send \"genOutsideAttack $1 $2 1\n\"
expect \"LOTUS >> \"
send \"run\n\"
expect \"LOTUS >> \"
send \"showASList sort best\n\"
expect \"LOTUS >> \"
send exit
exit 0
"
