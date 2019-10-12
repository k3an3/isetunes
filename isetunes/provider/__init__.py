from abc import ABC, abstractmethod


class Provider(ABC):
    @abstractmethod
    def search(self):
        raise NotImplemented

    @abstractmethod
    def get_album_art(self, album_id: str, image: int = 1):
        raise NotImplemented

    @abstractmethod
    def lookup(self, uri: str):
        raise NotImplemented
