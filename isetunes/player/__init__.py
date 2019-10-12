from abc import ABC, abstractmethod


class Player(ABC):
    @abstractmethod
    def get_current_track(self):
        pass

    @abstractmethod
    def get_state(self):
        pass

    @abstractmethod
    def play(self):
        pass

    @abstractmethod
    def pause(self):
        pass

    @abstractmethod
    def next(self):
        pass

    @abstractmethod
    def previous(self):
        pass

    @abstractmethod
    def stop(self):
        pass

    @abstractmethod
    def play(self):
        pass

    @abstractmethod
    def play(self):
        pass

    @abstractmethod
    def queue(self):
        pass

    @abstractmethod
    def play_next(self):
        pass

    @abstractmethod
    def set_volume(self):
        pass

    @abstractmethod
    def get_volume(self):
        pass
