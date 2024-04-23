from enum import Enum


class ConstellationType(Enum):
    """
    星座的类型：可能为极轨道星座, 可能为倾斜轨道星座
    """
    WALKER_STAR_CONSTELLATION = 1
    WALKER_DELTA_CONSTELLATION = 2
