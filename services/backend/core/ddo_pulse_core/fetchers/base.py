from __future__ import annotations

from abc import ABC, abstractmethod

from ddo_pulse_core.models import RawItem


class BaseFetcher(ABC):
    @abstractmethod
    def fetch(self, source_id: int, url: str, config_json: str) -> list[RawItem]:
        raise NotImplementedError
