import argparse
from os import path

from threading import Thread, Lock
from time import sleep
from warcio.warcwriter import WARCWriter
from warcio.statusandheaders import StatusAndHeaders

from url_normalize import url_normalize
from url_normalize.tools import deconstruct_url

from webPage import WebPage
from datetime import datetime, timedelta

import random
from time import time
# import yappi

class Crawler(Thread):

    PAGES_PER_DOC = 1000
    DEFAULT_DELAY = 0.1
    MAX_TRIES_PER_PAGE = 10
    MAX_DEPTH = 5
    SHUFFLE_PAGES = 250

    def __init__(self, id, max_pages, debug):
        Thread.__init__(self)
        self.id = id
        self.MAX_PAGES = max_pages
        self.DEBUG = debug

    def isOnDelay(self, page: WebPage, hostDelays: dict, ct: datetime):
        if page.host not in hostDelays.keys():
            return True

        delay = page.delayPolicy() or self.DEFAULT_DELAY
        delayDatetime = timedelta(seconds=delay)
        pageTime = datetime.fromtimestamp(hostDelays[page.host])
        
        if ct >= pageTime + delayDatetime:
            return True

        return False

    def writePageToFile(self, page: WebPage, warcWriter: WARCWriter):
        pageRaw = page.getRaw()
        headers_list = page.pageRequest.headers.items()

        http_headers = StatusAndHeaders(
            "200 OK", headers_list, protocol="HTTP/1.0")

        record = warcWriter.create_warc_record(page.pageURL, "response",
                                            payload=pageRaw,
                                            http_headers=http_headers)

        warcWriter.write_record(record)

    def getHost(self, pageURL):
        return url_normalize(deconstruct_url(pageURL).host)

    # check for URLS that splits in a lot of pages
    def isBlockedURLS(self, url: str):
        blocked_parts = ["strava.app.link", "booked", "nochi", "hotelmix", "javascript:"]
        blocked_ends = [".htm", ".onion", ".pdf"]

        for part in blocked_parts:
            if part in url: return True
        
        for end in blocked_ends:
            if end in url: return True
 
        return False

    def filterLinks(self, links, page, depth):
        filtered_links = []
        for link in links:
            # add page to visited to prevent adding duplicate pages
            if not self.isBlockedURLS(link):
                if self.getHost(link) == page.host and depth < self.MAX_DEPTH:
                    filtered_links.append([link, depth + 1])
                elif self.getHost(link) != page.host:
                    filtered_links.append([link, 0])

        return filtered_links

    def run(self):
        global count, queue, visited, hostDelays
        global outFile, writer
        global dataLock, writeLock

        queueTime = 0

        while (count < self.MAX_PAGES):
            try:
                url = None
                depth = 0
                page = None

                start = time()
                dataLock.acquire()
                queueTime += time() - start

                url, depth = queue.pop(0)

                # shuffle queue to prevent crawling the same host for a long time
                if count > 0 and count % self.SHUFFLE_PAGES == 0:
                    random.shuffle(queue)
                dataLock.release()

                page = WebPage(url)

                if url is None or not page.crawlable():
                    continue

                repeat = 0
                while repeat < self.MAX_TRIES_PER_PAGE:
                    try:
                        dataLock.acquire()

                        ct = datetime.now()
                        checkDelay = self.isOnDelay(page=page, hostDelays=hostDelays, ct=ct)
                        # store visit time if is on delay time
                        if checkDelay:
                            hostDelays[page.host] = ct.timestamp()

                        dataLock.release()

                        if checkDelay:
                            page.crawlPage()

                            if not page.isHTML:
                                break

                            if self.DEBUG:
                                page.printDebug(ct.timestamp())

                            writeLock.acquire()

                            if count >= self.MAX_PAGES:
                                writeLock.release()
                                break
                            
                            if count > 0 and count % self.PAGES_PER_DOC == 0:
                                print(f"File {int(count/self.PAGES_PER_DOC)}")
                                outFile.close()
                                outFile = open(f'corpus/crawl{int(count/self.PAGES_PER_DOC)}.warc.gz', 'wb')
                                writer = WARCWriter(outFile, gzip=True)
                            
                            self.writePageToFile(page=page, warcWriter=writer)
                            count+=1

                            writeLock.release()

                            links = page.getLinks()
                            filtered_links = self.filterLinks(links, page, depth)
                            
                            start = time()
                            dataLock.acquire()
                            queueTime += time() - start

                            filtered = [link for link in filtered_links if link[0] not in visited]
                            queue += filtered
                            visited.update([link[0] for link in filtered])

                            dataLock.release()
                            
                            break
                            
                    except:
                        repeat+=1
                        sleep(page.delayPolicy() or self.DEFAULT_DELAY)

            except:
                if dataLock.locked():
                    dataLock.release()

def parseInput():
    parser = argparse.ArgumentParser(description='IR input values')
    parser.add_argument('-s', dest='seeds', type=str, required=True,
                        help='the path to a file containing a list of seed URLs (one URL per line) for initializing the crawling process.')
    parser.add_argument('-n', dest='limit', type=int, required=True,
                        help='the target number of webpages to be crawled; the crawler should stop its execution once this target is reached.')
    parser.add_argument('-d', dest='debug', default=False, action='store_true')
    args = parser.parse_args()

    if not path.exists(args.seeds):
        print("Seeds file invalid")
        exit(1)

    with open(args.seeds, 'r') as seeds_f:
        seeds_arg = [line[:-1] for line in seeds_f.readlines()]
    
    return [seeds_arg, args.limit, args.debug]

if __name__ == "__main__":
    
    seeds, limit, debug = parseInput()

    count = 0
    queue = [[seed, 0] for seed in seeds]
    visited = set(seeds)
    hostDelays = {}

    dataLock = Lock()
    writeLock = Lock()

    print(f"File 0")
    outFile = open('corpus/crawl0.warc.gz', 'wb')
    writer = WARCWriter(outFile, gzip=True)

    threads = [Crawler(i, limit, debug) for i in range(100)]

    for t in threads:
        t.start()

    for t in threads:
        t.join()