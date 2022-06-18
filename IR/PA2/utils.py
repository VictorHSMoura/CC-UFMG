from math import ceil
from os import path, system

MEGABYTE = 1024 * 1024

def merge_docs(docs1, docs2):
    docs = ""
    d1 = 0
    d2 = 0

    while (d1 < len(docs1) and d2 < len(docs2)):
        if int(docs1[d1]) < int(docs2[d2]):
            docs += f"{docs1[d1]} {docs1[d1+1]} "
            d1 += 2
        elif int(docs1[d1]) > int(docs2[d2]):
            docs += f"{docs2[d2]} {docs2[d2+1]} "
            d2 += 2
        else:
            docs += f"{docs1[d1]} {docs1[d1+1]} "
            d1 += 2
            d2 += 2

    while d1 < len(docs1):
        docs += f"{docs1[d1]} {docs1[d1+1]} "
        d1 += 2

    while d2 < len(docs2):
        docs += f"{docs2[d2]} {docs2[d2+1]} "
        d2 += 2

    return docs + "\n"


def sort(f1, f2, step):
    f1_name = f"dumps/dump_{f1}_{step}.txt"
    f2_name = f"dumps/dump_{f2}_{step}.txt"

    file1 = open(f1_name, "r")
    file2 = open(f2_name, "r")

    merged = open(f"dumps/dump_{f1 // 2}_{step + 1}.txt", "w")

    l1 = file1.readline()
    l2 = file2.readline()
    while len(l1) > 0 or len(l2) > 0:
        if (len(l2) == 0):
            merged.write(l1)
            l1 = file1.readline()
        elif (len(l1) == 0):
            merged.write(l2)
            l2 = file2.readline()
        else:
            l1_key, l1_docs = l1.split(" ", 1)
            l2_key, l2_docs = l2.split(" ", 1)

            if l1_key < l2_key:
                merged.write(l1)
                l1 = file1.readline()
            elif l2_key < l1_key:
                merged.write(l2)
                l2 = file2.readline()
            else:
                docs = merge_docs(l1_docs.split(" ")[:-1], l2_docs.split(" ")[:-1])
                merged.write(f"{l1_key} {docs}")
                l1 = file1.readline()
                l2 = file2.readline()

    file1.close()
    file2.close()

    merged.close()
    system(f"rm -rf {f1_name} {f2_name}")

def merge(total_files, index_path):
    t = total_files
    step = 0
    
    while (t >= 2):
        if t % 2 != 0:
            system(f"mv dumps/dump_{t-1}_{step}.txt dumps/dump_{(t-1) // 2}_{step + 1}.txt")
        for i in range(1, t, 2):        
            sort(i-1, i, step)

        step += 1
        t = ceil(t/2)

    system(f"mv dumps/dump_0_{step}.txt {index_path}")
    

def calc_index_metric_and_seek(index_file):
    seek = 0
    path_dir = path.dirname(path.abspath(index_file))
    
    index_size = path.getsize(index_file)/ MEGABYTE
    n_list = 0
    total_size_list = 0
    with open(index_file, 'r') as index:
        with open(f'{path_dir}/seeks.txt', 'w') as s:
            while True:
                line = index.readline()
                if len(line) > 0:
                    term, docs = line.split(" ", 1)
                    s.write(f'{term} {seek}\n')
                    seek += len(line.encode('utf-8'))
                    
                    n_list += 1
                    docs = docs.split(" \n")[0]
                    total_size_list += len(docs.split(" ")) // 2
                else:
                    break

    return index_size, n_list, float(total_size_list)/n_list

def sort_page_list(f1, f2, step):
    f1_name = f"dumps/pages_{f1}_{step}.txt"
    f2_name = f"dumps/pages_{f2}_{step}.txt"

    file1 = open(f1_name, "r")
    file2 = open(f2_name, "r")

    merged = open(f"dumps/pages_{f1 // 2}_{step + 1}.txt", "w")

    l1 = file1.readline()
    l2 = file2.readline()
    while len(l1) > 0 or len(l2) > 0:
        if (len(l2) == 0):
            merged.write(l1)
            l1 = file1.readline()
        elif (len(l1) == 0):
            merged.write(l2)
            l2 = file2.readline()
        else:
            l1_key, _ = l1.split(" ", 1)
            l2_key, _ = l2.split(" ", 1)

            if int(l1_key) < int(l2_key):
                merged.write(l1)
                l1 = file1.readline()
            else:
                merged.write(l2)
                l2 = file2.readline()

    file1.close()
    file2.close()

    merged.close()
    system(f"rm -rf {f1_name} {f2_name}")

def merge_page_list(total_files, index_path):
    t = total_files
    step = 0
    
    while (t >= 2):
        if t % 2 != 0:
            system(f"mv dumps/pages_{t-1}_{step}.txt dumps/pages_{(t-1) // 2}_{step + 1}.txt")
        for i in range(1, t, 2):        
            sort_page_list(i-1, i, step)

        step += 1
        t = ceil(t/2)

    path_file = path.dirname(path.abspath(index_path))
    system(f"mv dumps/pages_0_{step}.txt {path_file}/page_list.txt")


def save_dict_and_page_list(word_dict: dict, page_list: list, id):
    keys_sorted = sorted(list(word_dict.keys()))
    f_name = f'dumps/dump_{id}_0.txt'
    p_name = f'dumps/pages_{id}_0.txt'

    with open(f_name, 'w') as f:
        for word in keys_sorted:
            f.write(f"{word} ")
            for doc in word_dict[word]:
                f.write(f"{doc[0]} {doc[1]} ")

            f.write("\n")

    with open(p_name, 'w') as f:
        for p in page_list:
            f.write(f"{p[0]} {p[1]} {p[2]}\n")