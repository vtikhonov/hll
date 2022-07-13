import hashlib
from typing import Optional

class Hash:
  def _create_hash(self, name: str, value: any) -> int:
    h = hashlib.new(name)
    h.update(str(value).encode("utf-8"))
    return int(h.hexdigest(), 16)

  def __init__(self, M: int, string_hash_name: Optional[str] = None) -> None:
    self.M = M
    self._range = 2**M
    self._max_value = self._range - 1

    self.string_hash_name = string_hash_name
    #self.string_hash = lambda x: self._create_hash(string_hash_name, x) if string_hash_name else hash(x)
    
    #mercenne prime is used for better diffusing
    self._mercenne = 2 ** 61 - 1

  def __eq__(self, other: 'Hash') -> bool:
    return self.M == other.M and self.string_hash_name == other.string_hash_name

  def get(self, v: any) -> int: 
    str_value = str(v)
    hash_value = self._create_hash(self.string_hash_name, str_value) if self.string_hash_name else hash(str_value)
    return hash_value % self._mercenne % self._range


def test_hash():
  h = Hash(8, "md5") #8-bit hash
  num_of_elements = 256
  hashes = {h.get(f"value_{i}") for i in range(num_of_elements)}
  assert len(hashes) > num_of_elements / 2, f"too many collisions {len(hashes)}"

if __name__ == "__main__":
  test_hash()