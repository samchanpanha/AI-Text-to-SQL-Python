from abc import ABC, abstractmethod


class DeliveryChannel(ABC):
    @abstractmethod
    def send(self, files: list[dict], task, **kwargs) -> dict:
        ...
