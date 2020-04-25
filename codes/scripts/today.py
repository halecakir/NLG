import os
import json


ANALYSIS_DIR = os.path.join(os.environ["NLG_ROOT"], "datasets/analysis")
DEX_DIR = os.path.join(ANALYSIS_DIR, "dex-analysis/")


def list_files(folder_name):
    files = [os.path.join(folder_name, f) \
            for f in os.listdir(folder_name) if os.path.isfile(os.path.join(folder_name, f))]
    return files


#For now just get the first file
dex_files = list_files(DEX_DIR)

print(dex_files)
# Get lib names
with open(dex_files[2], "r") as target:
    data = json.load(target)
    for k in data:
        print(k)
   # print(data['analytics-5.4.1'])
        

"""
{
            "name": "Adjust",
            "category": "Advertising",
            "comment": "",
            "repo": "http://jcenter.bintray.com",
            "groupid": "com.adjust.sdk",
            "artefactid": "adjust-android"
        }
{
            "name": "AppLovin",
            "category": "Advertising",
            "comment": "",
            "repo": "http://jcenter.bintray.com",
            "groupid": "com.applovin",
            "artefactid": "applovin-sdk"
        }
        {
            "name": "InMobi Mobile Ads",
            "category": "Advertising",
            "comment": "InMobi Ad Network and Rendering Framework",
            "repo": "http://jcenter.bintray.com",
            "groupid": "com.inmobi.monetization",
            "artefactid": "inmobi-ads"
        }
        {
            "name": "Flurry",
            "category": "Advertising",
            "comment": "",
            "repo": "http://jcenter.bintray.com",
            "groupid": "com.flurry.android",
            "artefactid": "ads"
        },
        {
            "name": "Umeng",
            "category": "Analytics",
            "comment": "",
            "repo": "http://jcenter.bintray.com",
            "groupid": "com.umeng.analytics",
            "artefactid": "analytics"
        },
        {
            "name": "Crittercism",
            "category": "Analytics",
            "comment": "",
            "groupid": "com.crittercism",
            "artefactid": "crittercism-android-agent",
            "repo": "mvn-central"
        },
        {
            "name": "HockeyApp",
            "category": "Analytics",
            "comment": "Microsoft HockeyApp: http://hockeyapp.net/features/",
            "groupid": "net.hockeyapp.android",
            "artefactid": "HockeySDK",
            "repo": "mvn-central"
        },
         {
        "name": "Amazon AWS Mobile Analytics",
        "category": "Analytics",
        "comment": "With Amazon Mobile Analytics, you can measure app usage and app revenue.",
        "groupid": "com.amazonaws",
        "artefactid": "aws-android-sdk-mobileanalytics",
        "repo": "mvn-central"
        }

        [{
    "name": "Amplitude",
    "category": "Analytics",
    "comment": "An Android SDK for tracking events and revenue to Amplitude",
    "repo": "http://jcenter.bintray.com",
    "groupid": "com.amplitude",
    "artefactid": "android-sdk"
},
{
    "name": "Tencent Map Geolocation",
    "category": "Analytics",
    "comment": "",
    "repo": "http://jcenter.bintray.com",
    "groupid": "com.tencent.map.geolocation",
    "artefactid": "TencentLocationSdk-meituandispatch"
},
{
    "name": "Flurry",
    "category": "Advertising",
    "comment": "",
    "repo": "http://jcenter.bintray.com",
    "groupid": "com.flurry.android",
    "artefactid": "analytics"
}]
"""