from os import path


N_DOCS = 950489

def create_mini_index(terms, index_file, keys):
    idx = {}
    with open(index_file, "r") as index:
        for term in terms:
            if term in keys:
                index.seek(keys[term])
                line = index.readline().split("\n")[0]
                if len(line) > 0:
                    t, docs = line.split(" ", 1)
                    docs = docs.split(" ")[:-1]
                    d = [[int(docs[i]), int(docs[i+1])] for i in range(0, len(docs), 2)]
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

def get_avgdl(index_file):
    avgdl = 0
    path_dir = path.dirname(path.abspath(index_file))
    with open(f'{path_dir}/page_list.txt', 'r') as f:
        for line in f:
            l = line.split("\n")[0]
            id, url, doc_size = l.split(" ")
            avgdl += int(doc_size)

    return avgdl / N_DOCS


def format_output(query, top10):
    print('{')
    print(f'\t"Query": "{query}",')
    print('\t"Results": [')
    for pos in top10:
        print(f'\t\t{{"URL": "{pos[2]}",')
        print(f'\t\t "Score": "{pos[1]:.5f}"}},')
    print('\t]')
    print('}')
