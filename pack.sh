#!/bin/bash
docker run --rm -it -v $PWD:/code nhl23 python3 pack.py $@
