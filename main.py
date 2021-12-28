from cmd import Cmd

class Interpreter(Cmd):
  intro = "=== This is ASPA simulator. ==="
  prompt = "aspa_simulation>> "

  def do_exit(self):
    return True

try:
  Interpreter().cmdloop()
except KeyboardInterrupt:
  print("\nKeyboard Interrupt (Ctrl+C)")
  pass
except:
  pass
