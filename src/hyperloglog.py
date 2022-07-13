from hash import Hash
from small_cells import SmallCells

from typing import Optional, Callable, Tuple
from array import array
import math
from functools import wraps
import time


class HyperLogLog:
    MIN_P = 4
    MAX_P = 16
    INT32_CEIL = 2**32

    @staticmethod
    def infer_log_of_number_of_counters(std_error: float) -> int:
        """
        Infers parameter `p` based on expected standard error
        """
        return math.ceil(math.log2((1.04/std_error)**2))

    __slots__ = ('M', 'p', 'm', 'fix_large_numbers', 'hash', 'counter_size', 'counters', '_internal_hash_length', '_internal_hash_length_mask')

    def __init__(self, M: int = 32, p: int = 5, hash: Optional[Hash] = None, fix_large_numbers: bool = False) -> None:
        assert M in [32, 64], f"Only 32 and 64 bit hashes are supported for HyperLogLog, but {M} provided"
        assert HyperLogLog.MIN_P <= p <= HyperLogLog.MAX_P, f"Incorrect number of bits used for bucketing: {p} is not in range [4, 16]"

        self.hash = hash if hash else Hash(M)
        self.p = p
        self.m = 2**p
        self.M = M
        self.fix_large_numbers = fix_large_numbers

        self.counter_size = math.ceil(math.log2(M - p + 1))
        #self.counters = array("B", [0 for _ in range(self.m)]) # this runs faster but takes 8 bits per cell, instead of 5
        self.counters = SmallCells(self.m, self.counter_size)

        self._internal_hash_length = self.M - self.p
        self._internal_hash_length_mask = (2**self._internal_hash_length)-1


    def volume_in_bytes(self) -> int:
        if hasattr(self.counters, 'volume_in_bytes'):
            return self.counters.volume_in_bytes()
        else:
            return self.m

    def add(self, value: any) -> 'HyperLogLog':
        h = self.hash.get(value)
        idx, hash_remainder = self._split_hash(h)
        rank = self._rank(hash_remainder)
        self.counters[idx] = max(self.counters[idx], rank)
        return self

    def merge(self, other: 'HyperLogLog') -> 'HyperLogLog':
        assert self.M == other.M, f"Inconsistent hash size: {self.M} vs {other.M}"
        assert self.m == other.m, f"Inconsistent buffer sizes: {self.m} vs {other.m}"
        assert self.hash == other.hash, f"Inconsistent hashes: {self.hash} vs {other.hash}"
        new_hll = HyperLogLog(self.M, self.p, self.hash)
        for counter_idx in range(self.m):
            new_hll.counters[counter_idx] = max(self.counters[counter_idx], other.counters[counter_idx])
        return new_hll

    def estimate_cardinality(self) -> int:
        """
        {\displaystyle E=\left(m\int _{0}^{\infty }\left(\log _{2}\left({\frac {2+u}{1+u}}\right)\right)^{m}\,du\right)^{-1} m^{2} \Bigg (}\sum _{j=1}^{m}{2^{-M[j]}}{\Bigg )}^{-1}}
        """
        r = sum([(2**(-self.counters[i])) for i in range(self.m)]) #(1/self.m)*
        z = (1/r)
        estimate = int(self._alpha_m() * (self.m**2) * z)

        v = len([1 for i in range(self.m) if self.counters[i] == 0])
        if estimate <= (5/2)*self.m and v > 0:
            #Linear counting provides more precise values for small cardinalities
            return int(self.m * math.log(self.m / v))
        elif self.fix_large_numbers and estimate > HyperLogLog.INT32_CEIL / 30:
            # for large cardinalities the estimation can be fixed.
            # in my test cases the fix did not improve the estimate, so I make it optional
            return self._fix_estimator_for_large_numbers(estimate)
        else:
            return estimate


    def _split_hash(self, h: int) -> Tuple[int, int]:
        return h >> self._internal_hash_length, h & self._internal_hash_length_mask

    def _fix_estimator_for_large_numbers(self, estimate: int) -> int:
        max_num = 2**32
        return int(-(max_num)*math.log(1 - (estimate/(max_num))))

    def _alpha_m(self) -> float:
        """
        Approximation of {\displaystyle \alpha _{m}=\left(m\int _{0}^{\infty }\left(\log _{2}\left({\frac {2+u}{1+u}}\right)\right)^{m}\,du\right)^{-1}}
        The alpha(m) is used for bias correction
        """
        if self.p == 4:
            return 0.673
        elif self.p == 5:
            return 0.697
        elif self.p == 6:
            return 0.709
        else:
            return (0.7213*self.m)/(self.m + 1.079)

    def _rank(self, hash: int) -> int:
        """
        Rank of a hash is its leftmost position of a set bit, using 1-base offset, 
        e.g. rank of a hash b'0011010001...' is 3, and rank(b'10001000...') == 1.
        It's the core of LogLog algorithm family: probability of rank value decreases exponentially:
        rank = 1 occurs in 50% cases
        rank = 2 occurs in 25% cases
        rank = 3 occurs in 12.5% cases
        """
        pos = 1
        for _ in range(self.M - self.p):
            if hash % 2 == 1:
                break
            else:
                hash = hash // 2
                pos += 1
        return pos


# def timeit(func):
#     @wraps(func)
#     def timeit_wrapper(*args, **kwargs):
#         start_time = time.perf_counter()
#         result = func(*args, **kwargs)
#         end_time = time.perf_counter()
#         total_time = end_time - start_time
#         print(f'Function {func.__name__}{args} {kwargs} Took {total_time:.4f} seconds')
#         return result
#     return timeit_wrapper

# def threshold(current_iteration: int) -> int:
#   if current_iteration < 1000:
#     return 50
#   elif current_iteration < 10000:
#     return 500
#   elif current_iteration < 100000:
#     return 5000
#   elif current_iteration < 1000000:
#     return 50000
#   elif current_iteration < 10000000:
#     return 500000
#   elif current_iteration < 100000000:
#     return 1000000
#   else:
#     return 2000000

def hll_test():
  h = Hash(32, "md5") 
  hll1 = HyperLogLog(p = 12, hash=h)
  hll2 = HyperLogLog(p = 12, hash=h)

  elements = [f"element_{i}" for i in range(100000)]
  elements_2k = [f"element_{i}" for i in range(2*100000)]

  for elem in elements:
    hll1.add(elem)

  for elem in elements_2k:
    hll2.add(elem)

  estimation1 = hll1.estimate_cardinality()
  estimation2 = hll2.estimate_cardinality()
  estimation_merged = hll1.merge(hll2).estimate_cardinality()

  assert 98000 <= estimation1 <= 102000, f"First estimation {estimation1} is inprecise"
  assert 195000 <= estimation2 <= 205000, f"Second estimation {estimation2} is inprecise"
  assert estimation_merged >= estimation1, "Second HLL must add some count, but it does not"
  assert estimation_merged == estimation2, "Violation: second HLL is a superset to the first one, so merged result shall reflect it, but it does not"
  assert estimation_merged < estimation1 + estimation2, "Set union violation"
  print("tests pass fine")

  # error_accum = 0
  # print(f"precis,hll_estimate,error,abs_error")
  # for i in range(2**32//1000000):
  #   hll.add(f"user_{i}")
  #   precise = i + 1
  #   if precise % threshold(i) == 0:
  #     estimate = hll.estimate_cardinality()
  #     error_accum += abs(estimate - precise)/precise
  #     ##print(f"precise = {precise}, estimate = {estimate}, error = {abs(estimate - precise)/precise}")
  #     relative_error = (estimate - precise)/precise
  #     print(f"{precise},{estimate},{relative_error},{abs(relative_error)}")

  # print(f"average error {error_accum / i}")
  
  # #print(h.get("value"))
  # print(hll.volume_in_bytes())
  # print(hll.estimate_cardinality(), i)


if __name__ == "__main__":
  hll_test()


  


"""
from hyperloglog import HyperLogLog, Hash
df = spark.range(1000000)
#rdd = df.rdd.map(lambda r: (r[0] % 7, f"user_{r[0]}")).aggregateByKey(HyperLogLog(32, 11, Hash(32, "md5")), lambda hll, element: hll1.add(element), lambda hll1, hll2: hll1.merge(hll2))
hll_res = df.rdd.map(lambda r: r[0]).aggregate(HyperLogLog(32, 11, Hash(32, "md5")), lambda hll, element: hll.add(element), lambda hll1, hll2: hll1.merge(hll2))
hll_res.estimate_cardinality()
"""
