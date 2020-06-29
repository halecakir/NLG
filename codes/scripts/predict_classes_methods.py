import os
import re
import json
import pandas as pd
import nltk 
import sys

sys.path.insert(0, "/home/huseyinalecakir/Security/SentenceOnlyAttentionDynet")
sys.path.insert(0, "/home/huseyinalecakir/NLG/codes/scripts/google_apis_crawler")

from models.model import load_model, predict_raw_sentence
from utils.io_utils import IOUtils
from utils.nlp_utils import NLPUtils

ANALYSIS_DIR = os.path.join(os.environ["NLG_ROOT"], "datasets/analysis")
DEX_DIR = os.path.join(ANALYSIS_DIR, "dex-analysis/DEXAnalysisResults")
OUTPUT_DIR = os.path.join(os.environ["NLG_ROOT"], "output/other")



class Arguments:
    permission_type = "READ_CONTACTS"
    saved_data = "/home/huseyinalecakir/datasets/saved-parameters/saved-data/ac-net/embeddings-sentences-w2i.pickle"
    model_checkpoint = "/home/huseyinalecakir/datasets/saved-parameters/saved-models/SentenceOnlyAttentionDyNET-bidirectional-gru-READ_CONTACTS.pt"
    outdir = "/home/huseyinalecakir/Security/output/SentenceOnlyAttentionDyNET/bidirectional-gru/READ_CONTACTS.out"
    encoder_dir = "bidirectional"
    encoder_type = "gru"
    num_epoch = 1
    stemmer = "porter"
    embedding_size = 300
    hidden_size = 128
    attention_size = 128
    init_weight = 0.08
    output_size = 1
    dropout = 0
    print_every = 1000


classes_dir = os.path.join(OUTPUT_DIR, "classes.csv")
methods_dir = os.path.join(OUTPUT_DIR, "methods.csv")

df_classes = pd.read_csv(classes_dir)
df_methods = pd.read_csv(methods_dir)

classes = df_classes.to_dict('records')
methods = df_methods.to_dict('records')

args = Arguments()
model = load_model(args)

def predict_descriptions(lst):
    for item in lst:
        description = item['description']
        if not pd.isna(description):
            sentences = nltk.sent_tokenize(description)
            if len(sentences) > 0:
                sentence = sentences[0]
                sent = NLPUtils.preprocess_sentence(sentence, args.stemmer)
                prediction = predict_raw_sentence(model,sent)
                item["prediction"] = prediction
            else:
                item["prediction"] = -1


def process_class_name(class_name):
    cls_name = class_name.replace("Class", "") \
                            .replace("extends", "") \
                            .replace("Enum", "") \
                            .replace("Builder", "") \
                            .replace("Interface", "")
    cls_name = re.sub('[^0-9a-zA-Z]+', ' ', cls_name)
    cls_name = cls_name.split()
    cls_name = [e for e in cls_name if len(e) > 1]
    tokens = []
    for e in cls_name:
        s = ""
        for c in e:
            if c.isupper():
                if s != "":
                    tokens.append(s)
                s = c
            else:
                s += c
        if s:
            tokens.append(s)
    tokens = [e.lower() for e in tokens]
    return tokens

def process_method_name(method_name):
    method_name = re.findall(r"[^\s]*\(.*\)", method_name)[0]
    method_name = method_name.split("(")[0]
    tokens = []
    s = ""
    for c in method_name:
        if c.isupper():
            if s != "":
                tokens.append(s)
            s = c
        else:
            s += c
    if s:
        tokens.append(s)
    tokens = [e.lower() for e in tokens]
    return tokens

def predict_class_and_method_signatures(lst):
    for item in lst:
        all_tokens = []
        class_name = item['class']
        if not pd.isna(class_name):
            tokens = process_class_name(class_name)
            all_tokens.extend(tokens)
        if 'method' in item:
            method_name = item['method']
            if not pd.isna(method_name):
                tokens = process_method_name(method_name)
                all_tokens.extend(tokens)
        signature = " ".join(all_tokens)
        sent = NLPUtils.preprocess_sentence(signature, args.stemmer)
        prediction = predict_raw_sentence(model,sent)
        item["prediction"] = prediction

predict_class_and_method_signatures(classes)
predict_class_and_method_signatures(methods)
#predict_descriptions(classes)
#predict_descriptions(methods)



classes_w_preds = pd.DataFrame(classes)
methods_w_preds = pd.DataFrame(methods)
classes_w_preds.sort_values(by=['prediction'], ascending=False).to_csv(os.path.join(OUTPUT_DIR, "classes_predictions_by_signature.csv"))
methods_w_preds.sort_values(by=['prediction'], ascending=False).to_csv(os.path.join(OUTPUT_DIR, "methods_predictions_by_signature.csv"))


