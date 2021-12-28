from cmd import Cmd

class AS_class_list:

  def __init__(self):
    self.class_list = {}

  def add_AS(self, as_number):
    self.class_list[as_number] = AS_class(as_number)

  def show_AS_list(self):
    for c in self.class_list.values():
      c.show_info()

class AS_class:
  def __init__(self, asn):
    self.as_number = asn
    self.network_address = "xxxx"
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
