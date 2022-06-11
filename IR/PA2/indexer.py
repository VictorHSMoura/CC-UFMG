import sys
from os import path
import resource
import argparse

from warcio.archiveiterator import ArchiveIterator
import nltk
from nltk.stem.rslp import *

MEGABYTE = 1024 * 1024
def memory_limit(value):
    limit = value * MEGABYTE
    resource.setrlimit(resource.RLIMIT_AS, (limit, limit))

def get_mem():
    with open('/proc/self/status') as f:
        memusage = f.read().split('VmRSS:')[1].split('\n')[0][:-3]

    return int(memusage.strip()) / 1024


def save_dict(word_dict, f_name = ''):
    with open(f_name, 'w') as f:
        for word in word_dict:
            f.write(f"{word} ")
            for doc in word_dict[word]:
                f.write(f"{doc[0]} {doc[1]} ")

            f.write("\n")

def build_index(total_mem, corpus_path):
    stemmer = RSLPStemmer()
    stopwords = set(nltk.corpus.stopwords.words('portuguese'))

    word_dict = {}
    page_id = 0
    dump_id = 0

    for i in range(2):
        with open(f"{corpus_path}/part-{i}.warc.gz.kaggle", "rb") as stream:
            for record in ArchiveIterator(stream):
                if record.rec_type == "response":
                    content = record.raw_stream.read().decode()
                    
                    stemmed = [stemmer.stem(word) for word in nltk.word_tokenize(content, language="portuguese")]
                    processed = [word for word in stemmed if word not in stopwords]

                    for word in set(processed):
                        if word not in word_dict:
                            word_dict[word] = []
                        word_dict[word].append([page_id, processed.count(word)])

                    if (get_mem() >= 0.7 * total_mem):
                        save_dict(word_dict=word_dict, f_name=f"dumps/dump_{dump_id}.txt")
                        word_dict.clear()
                        dump_id += 1

                    page_id += 1
                    
            if (len(word_dict) > 0):
                save_dict(word_dict, f_name=f'dumps/dump_{dump_id}.txt')


def main():
    """
    Your main calls should be added here
    """
    build_index(args.memory_limit, args.corpus_path)

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description='Process some integers.')
    parser.add_argument('-m', dest='memory_limit', action='store', required=True,
        type=int, help='memory available')
    parser.add_argument('-c', dest='corpus_path', type=str, required=True,
                        help='the path to a directory containing the corpus WARC files.')
    parser.add_argument('-i', dest='index_path', type=str, required=True,
                        help='the path to the index file to be generated.')
    args = parser.parse_args()

    if not path.exists(args.corpus_path):
        print("Corpus directory invalid")
        exit(1)

    memory_limit(args.memory_limit)
    try:
        main()
    except MemoryError:
        sys.stderr.write('\n\nERROR: Memory Exception\n')
        sys.exit(1)


# You CAN (and MUST) FREELY EDIT this file (add libraries, arguments, functions and calls) to implement your indexer
# However, you should respect the memory limitation mechanism and guarantee
# it works correctly with your implementation