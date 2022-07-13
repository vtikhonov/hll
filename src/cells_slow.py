import bitarray

"""
Array-like collection that stores logical entities of size smaller than byte, e.g. 5 bit cells

The implementation is memory-efficient, as it's based on bitarrays, though runtime is very inefficient:
more than 10x times slower than byte array, as each bit set/get operation adds overhead
"""
class CellCollection:
  __slots__ = ('m', 'c', 'bitarray')
  def __init__(self, m: int, c: int):
    self.m = m
    self.c = c
    self.bitarray = bitarray.bitarray(m*c)
    self.bitarray[:] = 0

  def volume_in_bytes(self) -> int:
    return self.m * self.c // 8
  
  def __getitem__(self, index: int) -> int:
    result = self.bitarray[index * self.c]
    for i in range(1, self.c):
      result = result * 2 + self.bitarray[index * self.c + i]
    return result

  def __setitem__(self, index: int, value: int):
    if value >= 2 ** self.c:
      print(f"The inserted value {value} exceeds available {self.c} bits")
    else:
      for i in range(self.c):
        b = value % 2
        value = value >> 1
        self.bitarray[index * self.c + self.c - i - 1] = b
