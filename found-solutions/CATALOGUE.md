Short-formula catalogue
=======================
7 formulas examined, 7 distinct structures.

Each row is the cheapest formula known to reach that structure. A candidate
matching one of these is scored as prior art unless it gets there in less code.

formula                                      cost              attractor   basin  mean
----------------------------------------------------------------------------------------
(1*asc -1*rev) % 10000                         44                 [0000]  1.0000  3.42
(1*rev -1*rot) % 10000                         48                 [0000]  1.0000  2.35
(1*desc -1*asc) % 10000                        47                 [6174]  0.9990  4.66
(-1*desc -1*ror + 495) % 10000                 68           [2370, 2938]  0.9903 94.22
(-2*rev -2*rot) % 10000                        50                 [2632]  0.9884 13.16
(2*ror -2*rot + 6174) % 10000                  68     [3600, 4888, 5382]  0.9863 14.50
(2*ror -1*asc + 495) % 10000                   64                 [3883]  0.9746 105.07