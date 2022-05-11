from io import BytesIO
import json

import requests
from bs4 import BeautifulSoup
from reppy.robots import Robots

from url_normalize import url_normalize
from url_normalize.tools import deconstruct_url

class WebPage:

    def __init__(self, pageURL: str):
        self.pageURL = pageURL
        self.host = url_normalize(deconstruct_url(self.pageURL).host)
        self.pageRequest = None
        self.html = ""
        self.isHTML = False
        self.timeout = 1
        self.userAgent = "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/101.0.4951.54 Safari/537.36"

        robots = Robots.fetch(
            Robots.robots_url(self.pageURL),
            timeout=self.timeout,
            headers={"User-Agent": self.userAgent}
        )
        self.agent = robots.agent(self.userAgent)

    def crawlable(self):
        return self.agent.allowed(self.pageURL)

    def delayPolicy(self):
        return self.agent.delay

    def crawlPage(self):
        req = requests.get(
            url=self.pageURL,
            headers={"Accept-Encoding": "identity", "User-Agent": self.userAgent},
            stream=True,
            timeout=self.timeout
        )

        if req is not None:
            self.pageRequest = req
            self.html = req.text
            self.isHTML = "text/html" in req.headers["content-type"]

            if self.isHTML:
                self.soup = BeautifulSoup(self.html, "html.parser")

    def getRaw(self):
        return BytesIO(bytes(self.html, "utf-8"))

    def normalizeLink(self, link: str):
        if link is None:
            return None
        
        if link.startswith("/"):
            return url_normalize(self.host[:-1] + link)
        elif link.startswith("#"):
            return None
        
        return url_normalize(link)

    def getLinks(self): 
        links = []
        for link in self.soup.find_all("a"):
            normalizedLink = self.normalizeLink(link.get("href"))
            if normalizedLink is not None:
                links.append(normalizedLink)

        return links

    def printDebug(self, timestamp):
        n_words = 20
        
        text = "" or self.soup.body.text.strip()
        if text != "":
            words = text.replace("\n", " ").replace("\t", " ").split(" ")
            words = [w.strip() for w in words if len(w.strip()) > 0]
            text =  " ".join(words[:n_words])

        title = "" or self.soup.title.text.strip()

        print(json.dumps({
            "URL": self.pageURL,
            "Title": title,
            "Text": text,
            "Timestamp": int(timestamp)
        }))