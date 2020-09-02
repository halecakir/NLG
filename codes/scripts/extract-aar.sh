LIB_PATH=/data/huseyinalecakir_data/my-lib-repo
find $LIB_PATH -name '*.aar' | while read line; do
    cd $(dirname $line)
    basename=$(basename $line)
    basename=${basename%".aar"}
    #echo $line
    jar xf $line
    rm {$basename}.jar
    mv classes.jar "$basename.jar"
done