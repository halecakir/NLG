from multiprocessing import Pool
import pickle

from CallGraph import call_script

def main(dataset):
    with Pool(processes=30) as pool:
        pool.map(call_script, dataset)
    

if __name__=="__main__":
    dataset = pickle.load( open( "dataset_for_app_analysis.p", "rb" ),encoding="bytes")
    main(dataset)
