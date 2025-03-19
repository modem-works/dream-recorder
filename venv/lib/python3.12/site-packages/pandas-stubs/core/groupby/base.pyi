from collections.abc import Hashable
import dataclasses

@dataclasses.dataclass(order=True, frozen=True)
class OutputKey:
    label: Hashable
    position: int
