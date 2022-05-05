from concurrent.futures import thread
from threading import Thread, Lock
from warcio.warcwriter import WARCWriter
from warcio.statusandheaders import StatusAndHeaders

from webPage import WebPage
from datetime import datetime, timedelta


class Crawler(Thread):

    def __init__(self):
        Thread.__init__(self)

    def isOnDelay(self, page: WebPage, hostDelays: dict, ct: datetime):
        if page.host not in hostDelays.keys():
            return True

        delay = page.delayPolicy() or 0.1
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

    def run(self):
        global count, queue, visited, hostDelays
        global outFile, writer
        global queueLock, secondaryLock, writeLock


        while (count < 1000):
            url = None
            page = None

            queueLock.acquire()
            if (len(queue) > 0):
                url = queue.pop(0)
                page = WebPage(url)
            queueLock.release()

            try:
                secondaryLock.acquire()
                checkPageVisited = url is not None and page.pageURL not in visited
                secondaryLock.release()

                if (checkPageVisited):
                    if(page.crawlable() and page.isHTML()):
                        secondaryLock.acquire()
                        ct = datetime.now()
                        checkDelay = self.isOnDelay(page=page, hostDelays=hostDelays, ct=ct)
                        secondaryLock.release()

                        if (checkDelay):
                            page.crawlPage()

                            if (page.pageRequest is not None):
                                
                                secondaryLock.acquire()
                                # check again if page was visited
                                if page.pageURL in visited:
                                    secondaryLock.release()
                                    continue

                                # add page to visited pages and store visit time
                                ct = datetime.now()
                                visited.add(page.pageURL)
                                hostDelays[page.host] = ct.timestamp()
                                secondaryLock.release()

                                links = page.getLinks()
                                
                                queueLock.acquire()
                                for link in links:
                                    if link not in visited:
                                        queue.append(link)
                                queueLock.release()

                                writeLock.acquire()
                                if count < 1000:
                                    print(page.pageURL)
                                    if (count > 0 and count % 100 == 0):
                                        print("Changing File")
                                        outFile.close()
                                        outFile = open(f'corpus/crawl{int(count/100)}.warc.gz', 'wb')
                                        writer = WARCWriter(outFile, gzip=True)
                                    
                                    self.writePageToFile(page=page, warcWriter=writer)
                                    count+=1
                                writeLock.release()
                                
                        else:
                            queueLock.acquire()
                            queue.append(url)
                            queueLock.release()
            except:
                if secondaryLock.locked():
                    secondaryLock.release()

count = 0
queue = ["https://g1.globo.com"]
visited = set()
hostDelays = {}

queueLock = Lock()
secondaryLock = Lock()
writeLock = Lock()

outFile = open('corpus/crawl0.warc.gz', 'wb')
writer = WARCWriter(outFile, gzip=True)

for i in range(100):
    t = Crawler()
    t.start()