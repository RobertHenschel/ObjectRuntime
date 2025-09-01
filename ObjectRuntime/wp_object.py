from typing import Optional


class WPObject:
    title: str
    host: Optional[str]
    port: Optional[int]

    def __init__(self, title: str, host: Optional[str] = None, port: Optional[int] = None) -> None:
        self.title = title
        self.host = host
        self.port = port

    def getTitle(self) -> str:
        return self.title

    def setHost(self, host: str) -> None:
        self.host = host

    def setPort(self, port: int) -> None:
        self.port = port


