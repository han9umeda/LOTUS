from cmd import Cmd

class AS_class_list:

  def __init__(self):
    self.class_list = {}

  def add_AS(self, as_number):
    self.class_list[as_number] = str(as_number)

  def get_AS_list(self):
    return self.class_list

class Interpreter(Cmd):
  intro = "=== This is ASPA simulator. ==="
  prompt = "aspa_simulation >> "

  def do_exit(self, line):
    return True

  def do_addAS(self, line):
    as_class_list.add_AS(line)

  def do_showASList(self, line):
    print(as_class_list.get_AS_list())

as_class_list = AS_class_list()

try:
  Interpreter().cmdloop()
except KeyboardInterrupt:
  print("\nKeyboard Interrupt (Ctrl+C)")
  pass
# except:
#   pass
