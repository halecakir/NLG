: '
# LibID
LIB_PATH=/data/huseyinalecakir_data/TEST_SET/apks
PROFILE_DIR=/data/huseyinalecakir_data/TEST_SET/decompiled
mkdir -p $PROFILE_DIR
find $LIB_PATH -name '*.apk' | while read line; do
    echo $line
    python ~/LibID/LibID.py profile -f $line -o $PROFILE_DIR
done
'

#LibRadar
conda deactivate
conda activate py27
APK_PATH=/data/huseyinalecakir_data/Downloads
PROFILE_DIR=/data/huseyinalecakir_data/LibRadar_Decompiled
mkdir -p $PROFILE_DIR
find $APK_PATH -name '*.apk' -printf "%f\n" | while read line; do
    echo $line
    python ~/LibRadar/LibRadar/libradar.py "${APK_PATH}/${line}" > "${PROFILE_DIR}/${line}.libradar"
done