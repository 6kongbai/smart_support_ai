import pytest
from typing import List


def jump(nums: List[int]) -> int:
    res = 0
    n = len(nums)
    maxpos = 0
    i = 0
    while i < n - 1:
        for j in range(i, min(maxpos + 1, n)):
            if maxpos < j + nums[j]:
                maxpos = j + nums[j]
                next_i = j

        i = min(next_i, n - 1)
        res += 1

    return res

