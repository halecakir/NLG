import os
import nltk
import pandas as pd

OUTPUT_DIR = os.path.join(os.environ["NLG_ROOT"], "output/other")

classes_dir = os.path.join(OUTPUT_DIR, "classes.csv")
methods_dir = os.path.join(OUTPUT_DIR, "methods.csv")

df_classes = pd.read_csv(classes_dir)
df_methods = pd.read_csv(methods_dir)

classes = df_classes.to_dict('records')
methods = df_methods.to_dict('records')

def filter_items(lst, keywords):
    filtered = []
    for item in lst:
        description = item['description']
        if not pd.isna(description):
            sentences = nltk.sent_tokenize(description)
            words = dict()
            for sentence in sentences:
                for token in nltk.word_tokenize(sentence.lower()):
                    if token not in words:
                        words[token] = 0
                    words[token] += 1
            for key in keywords:
                if key in words:
                    filtered.append(item)
                    break
    return filtered

keywords = ["permission"]
classes = filter_items(classes, keywords)
methods = filter_items(methods, keywords)

classes_filtered = pd.DataFrame(classes)
methods_filtered = pd.DataFrame(methods)
classes_filtered.to_excel(os.path.join(OUTPUT_DIR, "classes_filtered.xlsx"))
methods_filtered.to_excel(os.path.join(OUTPUT_DIR, "methods_filtered.xlsx"))

