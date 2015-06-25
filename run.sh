#!/bin/bash

while true
do
    git pull
    python3 run.py
    git add donations.json
    git add riders.json
    git commit -m 'auto update'
    git push
    sleep 300
done