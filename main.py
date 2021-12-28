import sys
from cmd import Cmd
import queue

class AS_class_list:
  def __init__(self):
    self.class_list = {}
    self.ip_gen = IP_address_generator()

  def add_AS(self, as_number):
    if not as_number in self.class_list.keys():
      self.class_list[as_number] = AS_class(as_number, self.ip_gen.get_unique_address())
    else:
      print("Error: AS " + str(as_number) + " is already registered.", file=sys.stderr)

  def show_AS_list(self, mode=""):
    if mode == "sort":
      keys = list(self.class_list.keys())
      keys.sort()
      for k in keys:
        self.class_list[k].show_info()
    else:
      for c in self.class_list.values():
        c.show_info()

class IP_address_generator:
  def __init__(self):
    self.index = 1 # To generate unique address

  def get_unique_address(self):
    address = "10." + str(self.index // 256) + "." + str(self.index % 256) + ".0/24"
    self.index += 1
    return address

class AS_class:
  def __init__(self, asn, address):
    self.as_number = asn
    self.network_address = address
    self.routing_table = {}
    self.policy = []

  def show_info(self):
    print(self.as_number)
    print(self.network_address)
    print(self.routing_table)
    print(self.policy)

class Interpreter(Cmd):
  def __init__(self):
    super().__init__()
    self.as_class_list = AS_class_list()
    self.message_queue = queue.Queue()

  intro = "=== This is ASPA simulator. ==="
  prompt = "aspa_simulation >> "

  def do_exit(self, line):
    return True

  def do_addAS(self, line):
    if line.isdecimal():
      self.as_class_list.add_AS(line)
    else:
      print("Error: Unknown Syntax", file=sys.stderr)

  def do_showASList(self, line):
    if line:
      if line == "sort":
        self.as_class_list.show_AS_list("sort")
      else:
        print("Error: Unknown Syntax", file=sys.stderr)
    else:
      self.as_class_list.show_AS_list()

  def do_registerMessage(self, line):
    try:
      if line == "":
        raise Exception
      param = line.split()
      if param[0] == "init" and len(param) == 2:      # ex) registerMessage init 12
        self.message_queue.put({"type":"init", "src": str(param[1])})
      elif param[0] == "update" and len(param) == 5:  # ex) registerMessage update 12 34 54-12 10.1.1.0/24
        self.message_queue.put({"type":"update", "src": str(param[1]), "dst": str(param[2]), "path": str(param[3]), "network": str(param[4])})
      else:
        raise Exception
    except Exception:
      print("Error: Unknown Syntax", file=sys.stderr)

  def do_showMessage(self, line):
    tmp_queue = queue.Queue()
    while not self.message_queue.empty():
      q = self.message_queue.get()
      print(q)
      tmp_queue.put(q)
    self.message_queue = tmp_queue


###
### MAIN PROGRAM
###


try:
  Interpreter().cmdloop()
except KeyboardInterrupt:
  print("\nKeyboard Interrupt (Ctrl+C)")
  pass
# except:
#   pass
