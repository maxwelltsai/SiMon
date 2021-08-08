from abc import ABC


class Callback(ABC):

    def __init__(self, **kwargs) -> None:
        super().__init__()
        self.kwargs = kwargs

    def run():
        pass 