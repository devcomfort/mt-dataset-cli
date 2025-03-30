from abc import ABC, abstractmethod

class WebParser(ABC):
    url: str
    
    def __init__(self, url: str):
        self.url = url

    @abstractmethod
    def fetch(self, url: str):
        """Fetch the web page and return the content"""
        pass

    @abstractmethod
    def parse(self):
        """Parse the web page and return a list of URLs"""
        pass
