# You can (and must) freely edit this file (add libraries, functions and calls) to implement your query processor
import argparse
from multiprocessing import Process, Lock, Value
from os import path
import re
from time import time

from warcio.archiveiterator import ArchiveIterator
import nltk
from nltk.stem.rslp import RSLPStemmer

NUM_PROCESS = 12
N_DOCS = 20000

def process_word(word):
    return re.sub(r"[^a-zA-Z\d\sãáàâéêíõóôúüç]", "", word)

def create_mini_index(terms, index_file):
    idx = {}
    with open(index_file, "r") as index:
        for term in terms:
            if term in keys:
                index.seek(keys[term])
                line = index.readline().split("\n")[0]
                if len(line) > 0:
                    t, docs = line.split(" ", 1)
                    docs = docs.split(" ")[:-1]
                    d = [[int(docs[i]), float(docs[i+1])] for i in range(0, len(docs), 2)]
                    idx[term] = d
    return idx

def find_doc(docs, doc):
    left, right = 0, len(docs) - 1

    while left <= right:
        middle = (left + right) // 2

        if docs[middle][0] == doc:
            return middle

        if docs[middle][0] < doc:
            left = middle + 1
        elif docs[middle][0] > doc:
            right = middle - 1
    
    return -1

def process_query(query, index_file):
    stemmer = RSLPStemmer()
    stopwords = set(nltk.corpus.stopwords.words('portuguese'))

    stemmed = [process_word(stemmer.stem(word)) for word in nltk.word_tokenize(query, language="portuguese") if word not in stopwords]
    processed = [word for word in stemmed if word != ""]
    
    results = []
    target = 0
    index = create_mini_index(processed, index_file)

    path_dir = path.dirname(path.abspath(index_file))
    with open(f'{path_dir}/page_list.txt', 'r') as f:
        for target in range(N_DOCS):
            l = f.readline().split("\n")[0]
            id, url, size = l.split(" ")

            score = 0
            for term in processed:
                if term in index:
                    docs = index[term]
                    doc_id = find_doc(docs, target)
                    if doc_id != -1:
                        score += (docs[doc_id][1] / float(size)) * float(N_DOCS/len(docs))

            results.append([target, score, url])

    return sorted(results, key=lambda x: -x[1])[:10]

def extract_index_keys(index_file):
    keys = {}
    seek = 0
    path_dir = path.dirname(path.abspath(index_file))
    with open(f'{path_dir}/seeks.txt', 'r') as index:
        while True:
            line = index.readline().split("\n")[0]
            if len(line) > 0:
                term, seek = line.split(" ")
                keys[term] = int(seek)
            else:
                break

    return keys

def format_output(query, top10):
    print('{')
    print(f'\t"Query": "{query}",')
    print('\t"Results": [')
    for pos in top10:
        print(f'\t\t{{"URL": "{pos[2]}",')
        print(f'\t\t "Score": "{pos[1]:.5f}"}}')
    print('\t]')
    print('}')


def parse_args():
    parser = argparse.ArgumentParser(description='Process some integers.')
    parser.add_argument('-i', dest='index_path', type=str, required=True,
                        help='the path to a index file.')
    parser.add_argument('-q', dest='queries', type=str, required=True,
                        help='the path to a file with the list of queries to process.')
    parser.add_argument('-r', dest='ranker', choices=['TFIDF', 'BM25'], required=True,
                        help='ranking function [TFIDF, BM25].')
    return parser.parse_args()

if __name__ == "__main__":
    args = parse_args()

    with open(args.queries, "r") as f:
        queries = f.readlines()
        keys = extract_index_keys(args.index_path)

        for query in queries:
            q = query.split("\n")[0]
            start = time()
            results = process_query(query=q, index_file=args.index_path)
            format_output(q, results)
            print(f"Total time: {time() - start}")