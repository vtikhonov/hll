# hll

Basic implementation of [https://en.wikipedia.org/wiki/HyperLogLog#Streaming_HLL](HyperLogLog)

## Fix for large numbers
![alt text](fix_large_numbers.png "Result of fixing large numbers")
In this example, where p=11, the fixing provide better results only in some range [140M - 1.7G]

## ToDo:
* Streaming variant to improve memory efficiency
* [https://en.wikipedia.org/wiki/HyperLogLog#Streaming_HLL](HyperLogLog++) for better accuracy on large cardinalities

