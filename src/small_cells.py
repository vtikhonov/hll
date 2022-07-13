from array import array
import math
from functools import reduce


"""
Array-like collection that stores logical entities of size smaller than byte, e.g. 5 bit cells
The implementation has same memory efficient as CellCollection, but runtime is up to 45% faster
"""
class SmallCells:
  __slots__ = ('m', 'c', 'masks', 'clear_masks', 'set_masks', 'array')
  
  def __init__(self, m: int, c: int):
    assert c < 8, "Use regular byte/short/int array for large cells"
    self.m = m
    self.c = c
    size = math.ceil(m * c / 8)
    self.masks = [(2**i - 1) for i in range(9)]
    self.clear_masks = [(256 - (2**i)) for i in range(8)]
    self.set_masks = [self._init_set_mask(i) for i in range(8)]
    self.array = array("B", [0 for _ in range(size)])

  def _init_set_mask(self, i: int) -> int:
    return (2**i - 1) | reduce(lambda a, b: a | b, [1<<i for i in range(i + self.c, 8)], 0)

  def volume_in_bytes(self) -> int:
    # ignore `m`, `c` and the masks fields, as their sizes do not depend on m/c, rather O(1)
    return len(self.array)
  
  def __getitem__(self, index: int) -> int:
    bit_index = index * self.c
    byte_index = bit_index >> 3
    byte_offset = bit_index & 7
    offset_end = byte_offset + self.c
    first_part = (self.array[byte_index] >> byte_offset) & self.masks[self.c]
    if offset_end <= 8:
      return first_part
    else:
      inverse_byte_offset = 8 - byte_offset
      second_part = (self.array[byte_index + 1] & self.masks[offset_end & 7]) << inverse_byte_offset
      #print(f"first({byte_index}): {self.array[byte_index]}, second({byte_index+1}) {self.array[byte_index+1]}, first_part {first_part}, second_part {second_part}, offset_end {offset_end}")
      return first_part | second_part

  def __setitem__(self, index: int, value: int) -> None:
    assert value <= self.masks[self.c], f"Integer overflow with number {value} for {self.c}-bit cells"
    bit_index = index * self.c
    byte_index = bit_index >> 3
    assert byte_index < len(self.array), "Index overflow"
    byte_offset = bit_index & 7
    offset_end = byte_offset + self.c
    inverse_byte_offset = 8 - byte_offset
    first_value_part = value & self.masks[inverse_byte_offset]
    self.array[byte_index] = (self.array[byte_index] & self.set_masks[byte_offset]) | (first_value_part << byte_offset)
    #print(f"for index {index}/{byte_index}, first_value_part {first_value_part}, value {value}, inverse_byte_offset {inverse_byte_offset}, new_value {new_value}")
    if offset_end > 8:
      second_value_part = value >> inverse_byte_offset
      self.array[byte_index + 1] = (self.array[byte_index + 1] & self.clear_masks[offset_end & 7]) | second_value_part
      

def test_cells():
  cell_count = 12
  cells = SmallCells(m = cell_count, c = 5)
  assert cells.volume_in_bytes() == 8

  for i in range(cell_count):
    assert cells[i] == 0, "Incorrectly initialized"
  

  for i in range(cell_count):
    cells[i] = i + 1 
  cells[2] = 15
  assert cells[1] == 2, "Setting an element affected the previous"
  assert cells[2] == 15, "Incorrectly set element"
  assert cells[3] == 4, "Setting an element affected the next element"

  try:
    overflow = False
    cells[5] = 32 # more than 5 bits can store
  except:
    overflow = True
  assert overflow, "Expected overflow exception but it did not happen"

  print("tests passed fine")

if __name__ == "__main__":
  test_cells()
