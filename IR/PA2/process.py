import sys
import resource
import argparse
from multiprocessing import Process

MEGABYTE = 1024 * 1024
def memory_limit(value):
    limit = value * MEGABYTE
    resource.setrlimit(resource.RLIMIT_AS, (limit, limit))

def main():
    """
    Your main calls should be added here
    """
    memory = 100
    p = Process(target=f, args=(memory,))
    p.start()
    p.join()


def f(memory):
    memory_limit(memory)
    try:
        print("I'm here!")
        a = ["foo"]
        while True:
            a += a*100
    except MemoryError:
        sys.stderr.write('\n\nERROR: Memory Exception in Process\n')
        sys.exit(1)

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description='Process some integers.')
    parser.add_argument(
        '-m',
        dest='memory_limit',
        action='store',
        required=True,
        type=int,
        help='memory available'
    )
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