import sys
sys.path.insert(0, "/home/huseyinalecakir/Security/SentenceOnlyAttentionDynet")
sys.path.insert(0, "/home/huseyinalecakir/NLG/codes/scripts/google_apis_crawler")

from models.model import load_model, predict_raw_sentence
from utils.io_utils import IOUtils
from utils.nlp_utils import NLPUtils

from google_apis_crawler.models import Class, Method, db_connect, create_table, Description
from sqlalchemy.orm import sessionmaker

import benepar
import nltk

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




def extract_vp(parent):
    if parent.label() == "VP":
        return " ".join(parent.leaves())
    for node in parent:
        if type(node) is nltk.Tree:
            if node.label() == "VP":
                return " ".join(node.leaves())
    return "-"

parser = benepar.Parser("benepar_en2")

args = Arguments()
model = load_model(args)

engine = db_connect()
create_table(engine)
Session = sessionmaker(bind=engine)
session = Session()

methods = session.query(Method).all()


for method in methods:
    description = method.description
    sentences = nltk.sent_tokenize(description)
    if len(sentences) > 0:
        sentence = sentences[0]
        try:
            tree = parser.parse(sentence)
        except ValueError:
            continue

        data = {}
        data["description"] = {"str" : sentence, "prediction" : -1}
        data["vp"] = {"str" : extract_vp(tree), "prediction" : -1}

        sent = NLPUtils.preprocess_sentence(data["description"]["str"], args.stemmer)
        data["description"]["prediction"] = predict_raw_sentence(model,sent)

        if data["vp"]["str"] != "-":
            sent = NLPUtils.preprocess_sentence(data["vp"]["str"], args.stemmer)
            data["vp"]["prediction"] = predict_raw_sentence(model,sent)

        d = Description(data)
        method.descriptions.append(d)
        try:
            session.add(d)
            session.commit()

        except:
            print("Database Error.")
            session.rollback()
            raise


