Domain results:
Domain              Sequence
    dw CCCGCACTTGTGCTTAGAAAC
   dw* GTTTCTAAGCACAAGTGCGGG
    dx    CTACCTTCAACCTCATCA
   dx*    TGATGAGGTTGAAGGTAG
  dx1m    CCCTACATCTCCACTCTA
 dx1m*    TAGAGTGGAGATGTAGGG
  dx2m    CCAACTCACTACTTCCAT
 dx2m*    ATGGAAGTAGTGAGTTGG
   dy1 CCCGTCAGGTCGATCAATGTT
  dy1* AACATTGATCGACCTGACGGG
   dy2 CCCAGCGAGTCCTAACGTATC
  dy2* GATACGTTAGGACTCGCTGGG

Strand results:
Strand                                Sequence
 base1 AACATTGATCGACCTGACGGGTGATGAGGTTGAAGGTAG
    y1                   CCCGTCAGGTCGATCAATGTT
 base2 GATACGTTAGGACTCGCTGGGTAGAGTGGAGATGTAGGG
    y2                   CCCAGCGAGTCCTAACGTATC
 base3 GTTTCTAAGCACAAGTGCGGGATGGAAGTAGTGAGTTGG
     w                   CCCGCACTTGTGCTTAGAAAC
     x                      CTACCTTCAACCTCATCA
   x1m                      CCCTACATCTCCACTCTA
   x2m                      CCAACTCACTACTTCCAT

Objective function:
                     Objective type  Value
           Weighted ensemble defect 0.0711
Soft constraints: energy difference 0.0106
Soft constraints: sequence symmetry  0.901
                              Total  0.983

Ensemble defect: 0.0711

Complex Complex defect (nt) Normalized complex defect
     G1                2.32                    0.0386
     G2                2.76                    0.0460
     G3                2.85                    0.0475
      W                1.94                    0.0922
      X               0.421                    0.0234
    X1m               0.282                    0.0157
    X2m               0.562                    0.0312
     Y1                3.83                     0.183
     Y2                3.13                     0.149

On-target complex defects:
Tube Tube defect (M) Normalized tube defect
  t1        2.11e-06                 0.0711

Tube defects:
Tube On-target complex Structural defect (M) Concentration defect (M) Total defect (M)
  t1                G1              2.30e-07                 2.98e-08         2.60e-07
  t1                G2              2.74e-07                 4.59e-08         3.20e-07
  t1                G3              2.84e-07                 2.05e-08         3.05e-07
  t1                 W              1.76e-07                 1.93e-07         3.69e-07
  t1                 X              4.20e-08                 5.68e-09         4.77e-08
  t1               X1m              2.81e-08                 7.41e-09         3.55e-08
  t1               X2m              5.58e-08                 1.34e-08         6.92e-08
  t1                Y1              3.82e-07                 6.18e-09         3.88e-07
  t1                Y2              3.13e-07                 2.81e-09         3.16e-07

On-target complex concentrations:
Tube Complex Concentration (M) Target concentration (M)
  t1      G1          9.95e-08                 1.00e-07
  t1      G2          9.92e-08                 1.00e-07
  t1      G3          9.97e-08                 1.00e-07
  t1       W          9.08e-08                 1.00e-07
  t1       X          9.97e-08                 1.00e-07
  t1     X1m          9.96e-08                 1.00e-07
  t1     X2m          9.93e-08                 1.00e-07
  t1      Y1          9.97e-08                 1.00e-07
  t1      Y2          9.99e-08                 1.00e-07

Significant off-target complex concentrations (>= 1% max complex concentration in tube):
Tube Complex Concentration (M)
  t1   (w+w)          4.53e-09
Complex results:
          Complex       Pfunc dG (kcal/mol)
0         (base1)   9.7554e+2        -4.242
1         (base2)   1.3634e+2        -3.029
2         (base3)   3.0958e+1        -2.116
3             (w)   2.5474e+0        -0.576
4             (x)   1.2588e+0        -0.142
5           (x1m)   1.1534e+0        -0.088
6           (x2m)   1.3175e+0        -0.170
7            (y1)   1.2725e+1        -1.568
8            (y2)   6.4846e+0        -1.152
9   (base1+base1)  1.6436e+10       -14.498
10  (base1+base2)  1.3230e+10       -14.364
11  (base1+base3)   7.8820e+8       -12.625
12      (base1+w)   1.1182e+8       -11.422
13      (base1+x)  7.0727e+18       -26.750
14    (base1+x1m)   2.7722e+8       -11.981
15    (base1+x2m)   2.8291e+8       -11.994
16     (base1+y1)  2.4478e+22       -31.773
17     (base1+y2)   2.0497e+8       -11.795
18  (base2+base2)   1.5773e+9       -13.053
19  (base2+base3)   3.4218e+8       -12.111
20      (base2+w)   4.0355e+7       -10.794
21      (base2+x)   2.0216e+8       -11.787
22    (base2+x1m)  3.2011e+18       -26.261
23    (base2+x2m)   3.5035e+8       -12.126
24     (base2+y1)   9.7343e+7       -11.336
25     (base2+y2)  1.7021e+22       -31.549
26  (base3+base3)   2.6122e+9       -13.364
27      (base3+w)  3.3039e+22       -31.957
28      (base3+x)   1.5809e+7       -10.216
29    (base3+x1m)   6.4192e+7       -11.080
30    (base3+x2m)  7.5348e+17       -25.370
31     (base3+y1)   8.5095e+7       -11.254
32     (base3+y2)   1.7204e+7       -10.268
33          (w+w)   1.9662e+8       -11.770
34          (w+x)   7.6519e+4        -6.931
35        (w+x1m)   1.6292e+5        -7.396
36        (w+x2m)   1.2683e+5        -7.242
37         (w+y1)   8.0929e+5        -8.384
38         (w+y2)   2.8657e+6        -9.164
39          (x+x)   2.4554e+3        -4.811
40        (x+x1m)   3.7008e+3        -5.064
41        (x+x2m)   4.7233e+3        -5.214
42         (x+y1)   1.2311e+6        -8.643
43         (x+y2)   1.3718e+5        -7.290
44      (x1m+x1m)   1.5897e+3        -4.543
45      (x1m+x2m)   3.6250e+3        -5.051
46       (x1m+y1)   1.1784e+6        -8.616
47       (x1m+y2)   3.3735e+5        -7.845
48      (x2m+x2m)   2.3065e+3        -4.772
49       (x2m+y1)   3.7999e+5        -7.918
50       (x2m+y2)   6.7297e+5        -8.271
51        (y1+y1)   6.7259e+7       -11.109
52        (y1+y2)   1.1367e+7       -10.013
53        (y2+y2)   1.8837e+6        -8.905
Concentration results:
      Complex   an1 (M)  
    (base3+w) 9.934e-08  
        (x2m) 9.934e-08  
   (base2+y2) 9.685e-08  
        (x1m) 9.685e-08  
   (base1+y1) 9.487e-08  
          (x) 9.487e-08  
    (base1+x) 5.128e-09  
         (y1) 5.126e-09  
  (base2+x1m) 3.150e-09  
         (y2) 3.149e-09  
  (base3+x2m) 6.600e-10  
          (w) 6.593e-10  
     (x1m+y1) 7.229e-13  
       (x+y1) 6.779e-13  
      (x+x2m) 4.867e-13  
     (x2m+y2) 4.468e-13  
      (x+x1m) 4.247e-13  
    (x1m+x2m) 4.162e-13  
        (x+x) 2.529e-13  
     (x1m+y2) 2.494e-13  
        (w+w) 2.389e-13  
    (x2m+x2m) 2.378e-13  
     (x2m+y1) 2.093e-13  
    (x1m+x1m) 2.033e-13  
      (y1+y1) 1.980e-13  
       (x+y2) 9.104e-14  
      (w+x1m) 6.421e-14  
      (w+x2m) 4.489e-14  
      (y1+y2) 4.033e-14  
        (w+x) 2.707e-14  
      (y2+y2) 8.055e-15  
       (w+y2) 6.532e-15  
       (w+y1) 1.530e-15  
      (base1) 5.175e-16  
      (base2) 8.809e-17  
      (base3) 1.983e-17  
  (base2+x2m) 3.095e-19  
  (base1+x1m) 2.239e-19  
  (base1+x2m) 2.052e-19  
    (base2+x) 1.785e-19  
  (base3+x1m) 6.261e-20  
    (base3+x) 1.384e-20  
   (base1+y2) 9.576e-22  
   (base2+y1) 4.595e-22  
   (base3+y1) 3.982e-22  
    (base1+w) 2.785e-22  
    (base2+w) 1.224e-22  
   (base3+y2) 9.704e-23  
(base1+base1) 8.389e-29  
(base1+base2) 8.224e-29  
(base3+base3) 1.944e-29  
(base2+base2) 1.194e-29  
(base1+base3) 4.857e-30  
(base2+base3) 2.568e-30  
dw CCCGCACTTGTGCTTAGAAAC
dw* GTTTCTAAGCACAAGTGCGGG
dx CTACCTTCAACCTCATCA
dx* TGATGAGGTTGAAGGTAG
dx1m CCCTACATCTCCACTCTA
dx1m* TAGAGTGGAGATGTAGGG
dx2m CCAACTCACTACTTCCAT
dx2m* ATGGAAGTAGTGAGTTGG
dy1 CCCGTCAGGTCGATCAATGTT
dy1* AACATTGATCGACCTGACGGG
dy2 CCCAGCGAGTCCTAACGTATC
dy2* GATACGTTAGGACTCGCTGGG
base1 AACATTGATCGACCTGACGGGTGATGAGGTTGAAGGTAG
y1 CCCGTCAGGTCGATCAATGTT
base2 GATACGTTAGGACTCGCTGGGTAGAGTGGAGATGTAGGG
y2 CCCAGCGAGTCCTAACGTATC
base3 GTTTCTAAGCACAAGTGCGGGATGGAAGTAGTGAGTTGG
w CCCGCACTTGTGCTTAGAAAC
x CTACCTTCAACCTCATCA
x1m CCCTACATCTCCACTCTA
x2m CCAACTCACTACTTCCAT