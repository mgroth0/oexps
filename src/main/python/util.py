"""
docstring
"""
from dataclasses import dataclass
# noinspection PyCompatibility
from pathlib import Path

import oexp

this_file = Path(__file__)


# noinspection PyMissingOrEmptyDocstring
def yaw(im):
    if isinstance(im,str):
        key = im
    else:
        key = str(im)
    return Orientation(key).yaw


# noinspection PyMissingOrEmptyDocstring
def pitch(im):
    if isinstance(im,str):
        key = im
    else:
        key = str(im)
    return Orientation(key).pitch


# noinspection PyCompatibility,PyMissingOrEmptyDocstring
@dataclass
class Orientation:
    key: str

    def __post_init__(self):
        key = self.key.replace(".png","")
        key = key.split("/")[-1]
        self.up = "U" in key
        self.left = "R" in key
        self.yaw = int(key[1:3])
        self.pitch = int(key[4:])

    def order_value(self):
        p_value = self.pitch * 1000
        if self.up:
            p_value *= -1
        y_value = self.yaw
        if self.left:
            y_value *= -1
        return p_value + y_value


# noinspection PyMissingOrEmptyDocstring
def custom_comparator(item: oexp.access.Choice):
    value = item.value
    o = Orientation(value)
    return o.order_value()
