import os
import subprocess
from multiprocessing import Pool

def attack(param):
  src = str(param[0])
  dst = str(param[1])
  print(f"attack src:{src} dst:{dst} START")
  filepath = os.path.join("data", f"result_src_{src}_dst_{dst}")
  with open(filepath, "w") as file:
    subprocess.run(["./jpnic_attack.sh", src, dst], stdout=file)

  with open(filepath, "r") as file:
    filedata = file.read()
  
  filedata.replace('\r', '')
  
  with open(filepath, "w") as file:
    file.write(filedata)
  print(f"attack src:{src} dst:{dst} FINISH")

if __name__ == '__main__':

  leaf_node_as_list = [24275, 59095, 131951, 63781, 131948, 59099, 37906, 63779, 18085, 55902, 58651, 59120]
  outside_connection_as_list = [2497, 2516, 2518, 2519, 4694, 4713, 4725, 7500, 7521, 7529, 7671, 7679, 7682, 7690, 9607, 9999, 10021, 17511, 17661, 17675, 17676, 17941, 23637, 24257, 24295, 55391, 55392, 55900, 59103, 59105, 131896, 131976, 2914]

  param = []
  for src in leaf_node_as_list:
    for dst in leaf_node_as_list:
      if src != dst:
        param.append([src, dst])

  p = Pool(3)
  p.map(attack, param)
