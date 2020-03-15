LIB_PATH=$NLG_ROOT/datasets/libraries/repo/
find $LIB_PATH -name '*.aar' | while read line; do
    cd $(dirname $line)
    jar xf $line
done