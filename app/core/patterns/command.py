from abc import ABC, abstractmethod
from typing import Any
from datetime import datetime


class Command(ABC):
    @abstractmethod
    def execute(self) -> None:
        pass

    @abstractmethod
    def undo(self) -> None:
        pass

    @abstractmethod
    def get_description(self) -> str:
        pass


class UpdateWeightCommand(Command):
    def __init__(
        self,
        config: dict[str, float],
        criterion_name: str,
        new_weight: float,
    ):
        self._config = config
        self._criterion_name = criterion_name
        self._new_weight = new_weight
        self._old_weight: float | None = None

    def execute(self) -> None:
        self._old_weight = self._config.get(self._criterion_name)
        self._config[self._criterion_name] = self._new_weight

    def undo(self) -> None:
        if self._old_weight is None:
            del self._config[self._criterion_name]
        else:
            self._config[self._criterion_name] = self._old_weight

    def get_description(self) -> str:
        return f"Update weight '{self._criterion_name}' from {self._old_weight} to {self._new_weight}"


class CommandHistory:
    def __init__(self):
        self._history: list[tuple[Command, datetime]] = []
        self._undo_stack: list[Command] = []

    def execute(self, command: Command) -> None:
        command.execute()
        self._history.append((command, datetime.now()))
        self._undo_stack.clear()

    def undo(self) -> bool:
        if not self._history:
            return False
        command, _ = self._history.pop()
        command.undo()
        self._undo_stack.append(command)
        return True

    def redo(self) -> bool:
        if not self._undo_stack:
            return False
        command = self._undo_stack.pop()
        command.execute()
        self._history.append((command, datetime.now()))
        return True

    def get_history_log(self) -> list[dict[str, Any]]:
        return [
            {"description": cmd.get_description(), "executed_at": ts.isoformat()}
            for cmd, ts in self._history
        ]
