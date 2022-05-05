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
            try:
                url = None
                page = None

                queueLock.acquire()
                if (len(queue) > 0):
                    url = queue.pop(0)
                    page = WebPage(url)
                queueLock.release()

                
                if(url is not None and page.crawlable() and page.isHTML()):
                    secondaryLock.acquire()
                    ct = datetime.now()
                    checkDelay = self.isOnDelay(page=page, hostDelays=hostDelays, ct=ct)
                    # store visit time if is on delay time
                    if checkDelay:
                        hostDelays[page.host] = ct.timestamp()
                    secondaryLock.release()

                    if (checkDelay):
                        page.crawlPage()

                        if (page.pageRequest is not None):
                            links = page.getLinks()
                            
                            queueLock.acquire()
                            for link in links:
                                # add page to visited to prevent adding duplicate pages
                                if link not in visited:
                                    queue.append(link)
                                    visited.add(link)
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
                if queue.locked():
                    queue.release()

count = 0
queue = ["https://g1.globo.com"]
visited = set("https://g1.globo.com")
hostDelays = {}

queueLock = Lock()
secondaryLock = Lock()
writeLock = Lock()

outFile = open('corpus/crawl0.warc.gz', 'wb')
writer = WARCWriter(outFile, gzip=True)

for i in range(100):
    t = Crawler()
    t.start()
