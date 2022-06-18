import gc
import sys
from os import path
import resource
import argparse
from time import time
from multiprocessing import Process, Lock, Value

from warcio.archiveiterator import ArchiveIterator
import nltk
from nltk.stem.rslp import RSLPStemmer

from utils import calc_index_metric_and_seek, merge, merge_page_list, save_dict_and_page_list

MEGABYTE = 1024 * 1024
NUM_PROCESS = 4
FILES = 96
PAGES_PER_FILE = 10000

dictionary = None

def memory_limit(value):
    limit = value * MEGABYTE
    resource.setrlimit(resource.RLIMIT_AS, (limit, limit))

def get_mem():
    with open('/proc/self/status') as f:
        memusage = f.read().split('VmRSS:')[1].split('\n')[0][:-3]

    return int(memusage.strip()) / 1024

def get_dict_size(word_dict):
    return sum([len(word_dict[word]) for word in word_dict])

def build_index(id, dump_id, memory, corpus_path, lock, start, end):
    memory_limit(memory)

    try:
        max_size = 2e6 * float(memory)/1024
        stemmer = RSLPStemmer()

        word_dict = {}
        page_list = []

        print(f"Process start: {id} / Memory limit: {memory}")

        for i in range(start, end):            
            page_id = PAGES_PER_FILE * i
            with open(f"{corpus_path}/part-{i}.warc.gz.kaggle", "rb") as stream:
                for record in ArchiveIterator(stream):
                    if record.rec_type == "response":
                        content = record.raw_stream.read().decode()
                        url = record.rec_headers.get_header('WARC-Target-URI')
                        
                        tokens = [stemmer.stem(word) for word in nltk.word_tokenize(content, language="portuguese")]
                        processed = [word for word in tokens if word != "" and word in dictionary]

                        for word in set(processed):
                            if word not in word_dict:
                                word_dict[word] = []
                            word_dict[word].append([page_id, processed.count(word)])

                        page_list.append([page_id, url, len(processed)])
                        

                        if (get_dict_size(word_dict) > max_size):
                            lock.acquire()
                            print(f"\nProcess {id} dump - MEM: {get_mem()}\n")
                            save_dict_and_page_list(word_dict=word_dict, page_list=page_list, id=dump_id.value)
                            dump_id.value += 1
                            
                            word_dict.clear()
                            page_list.clear()
                            gc.collect()

                            lock.release()

                        if page_id > 0 and page_id % 1000 == 0:
                            print(f"Process {id} - Page: {page_id}")
                            print(f"Real MEM: {get_mem()}\n")

                        page_id += 1
                    
                        
        if (len(word_dict) > 0):
            lock.acquire()

            save_dict_and_page_list(word_dict, page_list=page_list, id=dump_id.value)
            dump_id.value += 1

            lock.release()

    except MemoryError:
        sys.stderr.write('\n\nERROR: Memory Exception in Process\n')
        print(f"Process {id} - MEM: {get_mem()}")
        sys.exit(1)



def main():
    """
    Your main calls should be added here
    """
    processes = []
    lock = Lock()
    dump_id = Value('i', 0)

    global dictionary

    st = time()
    nltk_downloads()
    dictionary = get_dictionary()

    if not path.exists(args.corpus_path):
        print("Corpus directory invalid")
        exit(1)

    for p in range(NUM_PROCESS):
        start = round(p * (FILES / NUM_PROCESS))
        end = round((p + 1) * (FILES / NUM_PROCESS))
        processes.append(Process(target=build_index, args=(p, dump_id, args.memory_limit // NUM_PROCESS, args.corpus_path, lock, start, end)))

    for p in range(NUM_PROCESS):
        processes[p].start()

    for p in range(NUM_PROCESS):
        processes[p].join()

    merge(dump_id.value, args.index_path)
    size, n_list, avg = calc_index_metric_and_seek(args.index_path)
    merge_page_list(dump_id.value, args.index_path)
    
    print(f'{{ "Index Size": {int(size)},')
    print(f'  "Elapsed Time": {int(time() - st)},')
    print(f'  "Number of Lists": {n_list},')
    print(f'  "Average List Size": {avg:.2f}"}}')
    

def nltk_downloads():
    # necessary downloads
    nltk.download('punkt')
    nltk.download('rslp')
    nltk.download('stopwords')
    nltk.download('words')
    nltk.download('mac_morpho')

def get_dictionary():
    dictionary = set(word.lower() for word in nltk.corpus.words.words() if word)
    dictionary.update(word.lower() for word in nltk.corpus.floresta.words() if word)
    dictionary.update(word.lower() for word in nltk.corpus.mac_morpho.words() if word)

    stemmer = RSLPStemmer()
    stopwords = set(nltk.corpus.stopwords.words('portuguese'))
    return set(stemmer.stem(word) for word in dictionary if word not in stopwords)

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description='Process some integers.')
    parser.add_argument('-m', dest='memory_limit', action='store', required=True,
        type=int, help='memory available')
    parser.add_argument('-c', dest='corpus_path', type=str, required=True,
                        help='the path to a directory containing the corpus WARC files.')
    parser.add_argument('-i', dest='index_path', type=str, required=True,
                        help='the path to the index file to be generated.')
    args = parser.parse_args()

    memory_limit(args.memory_limit)
    try:
        
        main()
        
    except MemoryError:
        sys.stderr.write('\n\nERROR: Memory Exception\n')
        sys.exit(1)


# You CAN (and MUST) FREELY EDIT this file (add libraries, arguments, functions and calls) to implement your indexer
# However, you should respect the memory limitation mechanism and guarantee
# it works correctly with your implementation