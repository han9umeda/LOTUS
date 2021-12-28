from cmd import Cmd

class AS_class_list:
  def __init__(self):
    self.class_list = {}
    self.ip_gen = IP_address_generator()

  def add_AS(self, as_number):
    self.class_list[as_number] = AS_class(as_number, self.ip_gen.get_unique_address())

  def show_AS_list(self):
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
  intro = "=== This is ASPA simulator. ==="
  prompt = "aspa_simulation >> "

  def do_exit(self, line):
    return True

  def do_addAS(self, line):
    as_class_list.add_AS(line)

  def do_showASList(self, line):
    as_class_list.show_AS_list()

as_class_list = AS_class_list()

try:
  Interpreter().cmdloop()
except KeyboardInterrupt:
  print("\nKeyboard Interrupt (Ctrl+C)")
  pass
# except:
#   pass
