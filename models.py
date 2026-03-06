from dataclasses import dataclass
from typing import List, Tuple

@dataclass
class Ship:
    cells: List[Tuple[int, int]]
    hits: List[bool]
    horizontal: bool = True
    ship_type: str = ""
    
    def is_alive(self):
        return not all(self.hits)
    
    def get_size(self):
        return len(self.cells)
    
    def to_dict(self):
        return {
            "cells": self.cells,
            "hits": self.hits,
            "horizontal": self.horizontal
        }
    
    @classmethod
    def from_dict(cls, data):
        return cls(data["cells"], data["hits"], data["horizontal"])
    
    def __repr__(self):
        return f"Ship(size={self.get_size()}, cells={self.cells})"