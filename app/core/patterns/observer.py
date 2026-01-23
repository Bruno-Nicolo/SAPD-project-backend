from abc import ABC, abstractmethod


class WeightConfigObserver(ABC):
    @abstractmethod
    def on_weights_updated(self, weights: dict[str, float]) -> None:
        pass


class WeightConfigSubject:
    def __init__(self):
        self._observers: list[WeightConfigObserver] = []
        self._weights: dict[str, float] = {}

    def attach(self, observer: WeightConfigObserver) -> None:
        if observer not in self._observers:
            self._observers.append(observer)

    def detach(self, observer: WeightConfigObserver) -> None:
        self._observers.remove(observer)

    def notify(self) -> None:
        for observer in self._observers:
            observer.on_weights_updated(self._weights)

    def set_weights(self, weights: dict[str, float]) -> None:
        self._weights = weights
        self.notify()

    def get_weights(self) -> dict[str, float]:
        return self._weights.copy()


class ScoringModule(WeightConfigObserver):
    def __init__(self, module_name: str):
        self.module_name = module_name
        self._current_weights: dict[str, float] = {}

    def on_weights_updated(self, weights: dict[str, float]) -> None:
        self._current_weights = weights

    def get_current_weights(self) -> dict[str, float]:
        return self._current_weights.copy()
