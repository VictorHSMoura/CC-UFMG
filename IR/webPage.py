from io import BytesIO

import requests
from bs4 import BeautifulSoup
from reppy.robots import Robots

from url_normalize import url_normalize
from url_normalize.tools import deconstruct_url

class WebPage:

    def __init__(self, pageURL: str):
        self.pageURL = url_normalize(pageURL)
        self.host = url_normalize(deconstruct_url(self.pageURL).host)
        self.pageRequest = None
        self.html = ""
        self.userAgent = "victorBot"

        robots = Robots.fetch(Robots.robots_url(self.pageURL))
        self.agent = robots.agent(self.userAgent)

    def crawlable(self):
        return self.agent.allowed(self.pageURL)

    def delayPolicy(self):
        return self.agent.delay

    def crawlPage(self):
        self.pageRequest = requests.get(
            url=self.pageURL,
            headers={"Accept-Encoding": "identity", "User-Agent": self.userAgent},
            stream=True,
            timeout=1
        )

        if self.pageRequest is not None:
            self.html = self.pageRequest.text

    def isHTML(self):
        r = requests.head(self.pageURL)
        return "text/html" in r.headers["content-type"]

    def getRaw(self):
        return BytesIO(bytes(self.html, "utf-8"))

    def normalizeLink(self, link: str):
        if link is not None:
            if link.startswith("/"):
                return self.host[:-1] + link
            elif (link.startswith("#") or link.startswith("'")):
                return None
        
        return link

    def getLinks(self):
        soup = BeautifulSoup(self.html, "html.parser")

        links = []
        for link in soup.find_all("a"):
            normalizedLink = self.normalizeLink(link.get("href"))
            if normalizedLink is not None:
                links.append(normalizedLink)

        return links