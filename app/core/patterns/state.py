from __future__ import annotations
from abc import ABC, abstractmethod
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from app.core.patterns.state import Scorecard


class ScorecardState(ABC):
    @abstractmethod
    def edit(self, scorecard: Scorecard) -> None:
        pass

    @abstractmethod
    def submit_for_review(self, scorecard: Scorecard) -> None:
        pass

    @abstractmethod
    def certify(self, scorecard: Scorecard) -> None:
        pass

    @abstractmethod
    def deprecate(self, scorecard: Scorecard) -> None:
        pass

    @abstractmethod
    def get_state_name(self) -> str:
        pass


class DraftState(ScorecardState):
    def edit(self, scorecard: Scorecard) -> None:
        pass

    def submit_for_review(self, scorecard: Scorecard) -> None:
        scorecard.set_state(InReviewState())

    def certify(self, scorecard: Scorecard) -> None:
        raise InvalidStateTransitionError("Cannot certify a draft scorecard")

    def deprecate(self, scorecard: Scorecard) -> None:
        raise InvalidStateTransitionError("Cannot deprecate a draft scorecard")

    def get_state_name(self) -> str:
        return "Draft"


class InReviewState(ScorecardState):
    def edit(self, scorecard: Scorecard) -> None:
        scorecard.set_state(DraftState())

    def submit_for_review(self, scorecard: Scorecard) -> None:
        raise InvalidStateTransitionError("Already in review")

    def certify(self, scorecard: Scorecard) -> None:
        scorecard.set_state(CertifiedState())

    def deprecate(self, scorecard: Scorecard) -> None:
        raise InvalidStateTransitionError("Cannot deprecate a scorecard in review")

    def get_state_name(self) -> str:
        return "InReview"


class CertifiedState(ScorecardState):
    def edit(self, scorecard: Scorecard) -> None:
        raise InvalidStateTransitionError("Cannot edit a certified scorecard")

    def submit_for_review(self, scorecard: Scorecard) -> None:
        raise InvalidStateTransitionError("Already certified")

    def certify(self, scorecard: Scorecard) -> None:
        raise InvalidStateTransitionError("Already certified")

    def deprecate(self, scorecard: Scorecard) -> None:
        scorecard.set_state(DeprecatedState())

    def get_state_name(self) -> str:
        return "Certified"


class DeprecatedState(ScorecardState):
    def edit(self, scorecard: Scorecard) -> None:
        raise InvalidStateTransitionError("Cannot edit a deprecated scorecard")

    def submit_for_review(self, scorecard: Scorecard) -> None:
        raise InvalidStateTransitionError("Cannot submit deprecated scorecard")

    def certify(self, scorecard: Scorecard) -> None:
        raise InvalidStateTransitionError("Cannot certify deprecated scorecard")

    def deprecate(self, scorecard: Scorecard) -> None:
        raise InvalidStateTransitionError("Already deprecated")

    def get_state_name(self) -> str:
        return "Deprecated"


class InvalidStateTransitionError(Exception):
    pass


class Scorecard:
    def __init__(self, scorecard_id: str, product_name: str, score: float):
        self.scorecard_id = scorecard_id
        self.product_name = product_name
        self.score = score
        self._state: ScorecardState = DraftState()

    def set_state(self, state: ScorecardState) -> None:
        self._state = state

    def get_state_name(self) -> str:
        return self._state.get_state_name()

    def edit(self) -> None:
        self._state.edit(self)

    def submit_for_review(self) -> None:
        self._state.submit_for_review(self)

    def certify(self) -> None:
        self._state.certify(self)

    def deprecate(self) -> None:
        self._state.deprecate(self)
