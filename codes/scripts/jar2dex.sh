#!/bin/bash
LIB_PATH=$NLG_ROOT/datasets/libraries/repo/
find $LIB_PATH -name '*.jar' | while read line; do
    echo $line
    cd $(dirname $line)
    bash $NLG_EXTERNAL/LibID/dex2jar/d2j-jar2dex.sh  $line -o "classes.dex"
done
