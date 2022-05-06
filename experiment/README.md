# Target network information

## About

This directory has files for experiment on evaluation of ASPA.

 - jpnic\_network.yml: This file represents AS network composed of JPNIC-registered ASes and 1 Global Tier-1 AS (AS2914 GIN). The data is from [BGPview](https://bgpview.io/) at 2021-12-14. File format is LOTUS-importable YAML format.
 - jpnic\_attack.sh: Attack simulation that targets JPNIC Network and normal attack from 1st argument AS to 2nd argument AS.
 - jpnic\_outside\_attack.sh: Attack simulation that targets JPNIC Network and outside attack via 1st argument AS to 2nd argument AS.
 - jpnic\_attack\_aspa\_aspv.sh: Attack simulation that targets JPNIC Network with ASPA and ASPV and normal attack from 1st argument AS to 2nd argument AS.

## Intended use

Each simulation is light enough to execute parallel, so we recommend to use parallel execution (like, Python multiprocessing library or `xargs` command).
We prepare parallel execution script using Python multiprocessing library.
Execution image is below.

```
             +---> |jpnic_attack.sh|
             |
|multi.py| --+---> |jpnic_attack.sh|
             |
             +---> |jpnic_attack.sh|
```

## experiment situation information

### Leaf-node ASes

 - 24275
 - 59095
 - 131951
 - 63781
 - 131948
 - 59099
 - 37906
 - 63779
 - 18085
 - 55902
 - 58651
 - 59120

### Outside connection ASes

 - 2497
 - 2516
 - 2518
 - 2519
 - 4694
 - 4713
 - 4725
 - 7500
 - 7521
 - 7529
 - 7671
 - 7679
 - 7682
 - 7690
 - 9607
 - 9999
 - 10021
 - 17511
 - 17661
 - 17675
 - 17676
 - 17941
 - 23637
 - 24257
 - 24295
 - 55391
 - 55392
 - 55900
 - 59103
 - 59105
 - 131896
 - 131976
 - 2914
