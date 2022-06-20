# You can (and must) freely edit this file (add libraries, functions and calls) to implement your query processor
import argparse
from math import log
from multiprocessing import Process, Lock
from os import path

import nltk
from nltk.stem.rslp import RSLPStemmer

from utils_processor import N_DOCS, create_mini_index, extract_index_keys, find_doc, format_output, get_avgdl

NUM_PROCESS = 12

def process_query(query, index_file, ranker):
    stemmer = RSLPStemmer()
    stopwords = set(nltk.corpus.stopwords.words('portuguese'))

    stemmed = [stemmer.stem(word) for word in nltk.word_tokenize(query, language="portuguese") if word not in stopwords]
    processed = [word for word in stemmed if word != ""]
    
    results = []
    target = 0
    index = create_mini_index(processed, index_file, keys)

    path_dir = path.dirname(path.abspath(index_file))
    # for BM25
    k = 1.2
    b = 0.75

    with open(f'{path_dir}/page_list.txt', 'r') as f:
        for line in f:
            l = line.split("\n")[0]
            id, url, doc_size = l.split(" ")
            
            target = int(id)
            doc_size = float(doc_size)
            score = 0
            
            for term in processed:
                if term in index:
                    docs = index[term]
                    doc_id = find_doc(docs, target)
                    if doc_id == -1:
                        score = 0
                        break

                    f = docs[doc_id][1]
                    idf = log(N_DOCS/float(len(docs)))

                    if ranker == "TFIDF":
                        tf = f / doc_size
                        score +=  tf * idf
                    else:
                        score += idf * (f * (k + 1)) / (f + k * (1 - b + (b * doc_size/avgdl)))


            results.append([target, score, url])

    return sorted(results, key=lambda x: -x[1])[:10]

def process_list_of_queries(queries, index_file, ranker, lock_print):
    for query in queries:
        results = process_query(query=query, index_file=index_file, ranker=ranker)
        
        lock_print.acquire()
        format_output(query, results)
        lock_print.release()


def parse_args():
    parser = argparse.ArgumentParser(description='Process some integers.')
    parser.add_argument('-i', dest='index_path', type=str, required=True,
                        help='the path to a index file.')
    parser.add_argument('-q', dest='queries', type=str, required=True,
                        help='the path to a file with the list of queries to process.')
    parser.add_argument('-r', dest='ranker', choices=['TFIDF', 'BM25'], required=True,
                        help='ranking function [TFIDF, BM25].')
    return parser.parse_args()

def nltk_downloads():
    # necessary downloads
    nltk.download('punkt', quiet=True)
    nltk.download('rslp', quiet=True)
    nltk.download('stopwords', quiet=True)
    nltk.download('words', quiet=True)

if __name__ == "__main__":
    args = parse_args()

    nltk_downloads()

    keys = extract_index_keys(args.index_path)
    avgdl = 0.0
    if args.ranker == "BM25":
        avgdl = get_avgdl(args.index_path)

    with open(args.queries, "r") as f:
        queries = f.readlines()
        queries = [ query.split("\n")[0] for query in queries ]

        processes = []
        lock = Lock()

        for p in range(NUM_PROCESS):
            start = round(p * (len(queries) / NUM_PROCESS))
            end = round((p + 1) * (len(queries) / NUM_PROCESS))
            processes.append(Process(target=process_list_of_queries, args=(queries[start:end], args.index_path, args.ranker, lock)))

        for p in range(NUM_PROCESS):
            processes[p].start()

        for p in range(NUM_PROCESS):
            processes[p].join()
            