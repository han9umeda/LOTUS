import sys
import re
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

  def get_AS(self, as_number):
    return self.class_list[as_number]

  def get_AS_list(self):
    return self.class_list

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
    self.policy = ["LocPrf", "PathLength"]
    self.routing_table = Routing_table(self.network_address, self.policy)

  def show_info(self):
    print(self.as_number)
    print(self.network_address)
    print(self.routing_table.get_table())
    print(self.policy)

  def set_public_aspa(self, public_aspa_list):
    self.routing_table.set_public_aspa(public_aspa_list)

  def update(self, update_message):
    if self.as_number in update_message["path"].split("-"):
      return

    route_diff = self.routing_table.update(update_message)
    if route_diff == None:
      return
    else:
      route_diff["path"] = str(self.as_number) + "-" + route_diff["path"]
      return route_diff

  def change_ASPV(self, message):
    if message["switch"] == "on":
      self.policy = ["LocPrf", "PathLength"]
      self.policy.insert(int(message["priority"]) - 1, "aspv")
    elif message["switch"] == "off":
      self.policy = ["LocPrf", "PathLength"]
    self.routing_table.change_policy(self.policy)

  def receive_init(self, init_message):
    best_path_list = self.routing_table.get_best_path_list()
    new_update_message_list = []
    update_src = self.as_number
    update_dst = init_message["src"]
    if init_message["come_from"] == "customer":
      for r in best_path_list:
        if r["path"] == "i": # the network is the AS itself
          new_update_message_list.append({"src": update_src, "dst": update_dst, "path": update_src, "network": r["network"]})
        else:
          new_update_message_list.append({"src": update_src, "dst": update_dst, "path": update_src + "-" + r["path"], "network": r["network"]})
    else:
      for r in best_path_list:
        if r["come_from"] == "customer":
          if r["path"] == "i": # the network is the AS itself
            new_update_message_list.append({"src": update_src, "dst": update_dst, "path": update_src, "network": r["network"]})
          else:
            new_update_message_list.append({"src": update_src, "dst": update_dst, "path": update_src + "-" + r["path"], "network": r["network"]})
    return new_update_message_list

class Routing_table:
  def __init__(self, network, policy):
    self.table = {}
    self.table[network] = [{"path": "i", "come_from": "customer", "LocPrf": 1000, "best_path": True}]
    self.policy = policy
    self.public_aspa_list = {}

  def change_policy(self, policy):
    self.policy = policy

  def set_public_aspa(self, public_aspa_list):
    self.public_aspa_list = public_aspa_list

  def aspv(self, route):
    if route["come_from"] == "customer":
      print("DEBUG in aspv")
      return route
    else:
      return route

  def update(self, update_message):
    network = update_message["network"]
    path = update_message["path"]
    come_from = update_message["come_from"]

    if come_from == "peer":
      locpref = 100
    elif come_from == "provider":
      locpref = 50
    elif come_from == "customer":
      locpref = 200

    new_route = {"path": path, "come_from": come_from, "LocPrf": locpref}

    if "aspv" in self.policy:
      new_route = self.aspv(new_route)

    try:
      new_route["best_path"] = False
      self.table[network].append(new_route)

      # select best path
      best = None
      for r in self.table[network]:
        if r["best_path"] == True:
          best = r
          break

      for p in self.policy:
        if p == "LocPrf":
          if new_route["LocPrf"] > best["LocPrf"]:
            new_route["best_path"] = True
            best["best_path"] = False
            return {"path": new_route["path"], "come_from": new_route["come_from"], "network": network}
          elif new_route["LocPrf"] == best["LocPrf"]:
            continue
          elif new_route["LocPrf"] < best["LocPrf"]:
            return None
        elif p == "PathLength":
          new_length = len(new_route["path"].split("-"))
          best_length = len(best["path"].split("-"))
          if new_length < best_length:
            new_route["best_path"] = True
            best["best_path"] = False
            return {"path": new_route["path"], "come_from": new_route["come_from"], "network": network}
          elif new_length == best_length:
            continue
          elif new_length > best_length:
            return None

    except KeyError:
      new_route["best_path"] = True
      self.table[network] = [new_route]
      return {"path": path, "come_from": come_from, "network": network}

  def get_best_path_list(self):

    best_path_list = []

    for network in self.table.keys():
      for route in self.table[network]:
        if route["best_path"] == True:
          best_path_list.append(dict({"network": network}, **route))

    return best_path_list

  def get_table(self):
    return self.table

class ASPAInputError(Exception):
  # Exception class for application-dependent error
  pass

class Interpreter(Cmd):
  def __init__(self):
    super().__init__()
    self.as_class_list = AS_class_list()
    self.message_queue = queue.Queue()
    self.connection_list = []
    self.public_aspa_list = {}

  intro = "=== This is ASPA simulator. ==="
  prompt = "aspa_simulation >> "

  def do_exit(self, line):
    return True

  def do_addAS(self, line):
    if line.isdecimal():
      self.as_class_list.add_AS(line)
    else:
      print("Usage: addAS [asn]", file=sys.stderr)

  def do_showAS(self, line):
    if line.isdecimal():
      try:
        self.as_class_list.get_AS(line).show_info()
      except KeyError:
        print("Error: AS " + str(line) + " is NOT registered.", file=sys.stderr)
    else:
      print("Usage: addAS [asn]", file=sys.stderr)

  def do_showASList(self, line):
    if line:
      if line == "sort":
        self.as_class_list.show_AS_list("sort")
      else:
        print("Error: Unknown Syntax", file=sys.stderr)
    else:
      self.as_class_list.show_AS_list()

  def do_addMessage(self, line):
    try:
      if line == "":
        raise ASPAInputError
      param = line.split()
      if len(param) == 2 and param[0] == "init" and param[1].isdecimal():          # ex) addMessage init 12
        self.message_queue.put({"type": "init", "src": str(param[1])})
      elif len(param) == 5 and param[0] == "update" and param[1].isdecimal() and \
           param[2].isdecimal() and re.fullmatch("((25[0-5]|2[0-4][0-9]|1[0-9][0-9]|[1-9]?[0-9])\.){3}(25[0-5]|2[0-4][0-9]|1[0-9][0-9]|[1-9]?[0-9])/[0-9][0-9]" , param[4]): # ex) addMessage update 12 34 54-12 10.1.1.0/24
        self.message_queue.put({"type": "update", "src": str(param[1]), "dst": str(param[2]), "path": str(param[3]), "network": str(param[4])})
      else:
        raise ASPAInputError
    except ASPAInputError:
      print("Usage: addMessage init [src_asn]", file=sys.stderr)
      print("       addMessage update [src_asn] [dst_asn] [path] [network]", file=sys.stderr)

  def do_addAllASInit(self, line):
    for as_number in self.as_class_list.get_AS_list().keys():
      self.message_queue.put({"type": "init", "src": as_number})

  def do_showMessage(self, line):
    tmp_queue = queue.Queue()
    while not self.message_queue.empty():
      q = self.message_queue.get()
      print(q)
      tmp_queue.put(q)
    self.message_queue = tmp_queue

  def do_addConnection(self, line):
    try:
      param = line.split()
      if len(param) == 3 and param[1].isdecimal() and param[2].isdecimal():
        if param[0] == "peer":
          self.connection_list.append({"type": "peer", "src": param[1], "dst": param[2]})
        elif param[0] == "down":
          self.connection_list.append({"type": "down", "src": param[1], "dst": param[2]})
        else:
          raise ASPAInputError
      else:
        raise ASPAInputError
    except ASPAInputError:
      print("Usage: addConnection peer [src_asn] [dst_asn]", file=sys.stderr)
      print("       addConnection down [src_asn] [dst_asn]", file=sys.stderr)

  def do_showConnection(self, line):
    for c in self.connection_list:
      print(c)

  def do_addASPA(self, line):
    param = line.split()
    try:
      if len(param) < 2:
        raise ASPAInputError
      else:
        for p in param:
          if not p.isdecimal():
            raise ASPAInputError
      self.public_aspa_list[param[0]] = param[1:]
    except ASPAInputError:
      print("Usage: addASPA [customer_asn] [provider_asns...]")

  def do_showASPA(self, line):
    if line == "":
      print(self.public_aspa_list)
    else:
      try:
        print(self.public_aspa_list[line])
      except KeyError:
        print("Error: Unknown Syntax", file=sys.stderr)

  def do_setASPV(self, line):
    param = line.split()
    try:
      if len(param) < 2:
        raise ASPAInputError
      if not param[0].isdecimal():
        raise ASPAInputError
      as_class = self.as_class_list.get_AS(param[0])
      if param[1] == "on":
        if re.fullmatch("1|2|3", param[2]):
          as_class.change_ASPV({"switch": "on", "priority": param[2]})
        else:
          raise ASPAInputError
      elif param[1] == "off":
        as_class.change_ASPV({"switch": "off"})
      else:
        raise ASPAInputError

    except ASPAInputError:
      print("Usage: setASPV [asn] on [1/2/3]", file=sys.stderr)
      print("       setASPV [asn] off", file=sys.stderr)
    except KeyError:
      print("Error: AS " + str(param[0]) + " is NOT registered.", file=sys.stderr)

  def get_connection_with(self, as_number):
    c_list = []
    for c in self.connection_list:
      if as_number in [c["src"], c["dst"]]:
        c_list.append(c)
    return c_list

  def as_a_is_what_on_c(self, as_a, connection_c):
    if connection_c["type"] == "peer":
      return "peer"
    elif connection_c["type"] == "down":
      if as_a == connection_c["src"]:
        return "provider"
      elif as_a == connection_c["dst"]:
        return "customer"

  def do_run(self, line):

    for as_class in self.as_class_list.get_AS_list().values(): # To reference public_aspa_list when ASPV
      as_class.set_public_aspa(self.public_aspa_list)

    while not self.message_queue.empty():
      m = self.message_queue.get()
      if m["type"] == "update":
        as_class = self.as_class_list.get_AS(m["dst"])

        # search src-dst connection
        connection_with_dst = self.get_connection_with(m["dst"])
        connection = None
        for c in connection_with_dst:
          if m["src"] in [c["src"], c["dst"]]:
            connection = c
            break

        # peer, customer or provider
        m["come_from"] = self.as_a_is_what_on_c(m["src"], connection)

        route_diff = as_class.update(m)
        if route_diff == None:
          continue
        if route_diff["come_from"] == "customer":
          for c in connection_with_dst:
            new_update_message = {}
            new_update_message["type"] = "update"
            new_update_message["src"] = m["dst"]
            new_update_message["path"] = route_diff["path"]
            new_update_message["network"] = route_diff["network"]
            tmp = [c["src"], c["dst"]]
            tmp.remove(m["dst"])
            new_update_message["dst"] = tmp[0]
            self.message_queue.put(new_update_message)
        elif route_diff["come_from"] == "peer" or route_diff["come_from"] == "provider":
          for c in connection_with_dst:
            if c["type"] == "down" and c["src"] == m["dst"]:
              new_update_message = {}
              new_update_message["type"] = "update"
              new_update_message["src"] = m["dst"]
              new_update_message["dst"] = c["dst"]
              new_update_message["path"] = route_diff["path"]
              new_update_message["network"] = route_diff["network"]
              self.message_queue.put(new_update_message)

      elif m["type"] == "init":
        for c in self.get_connection_with(m["src"]):
          m["come_from"] = self.as_a_is_what_on_c(m["src"], c)
          tmp = [c["src"], c["dst"]]
          tmp.remove(m["src"])
          new_update_message_list = self.as_class_list.get_AS(tmp[0]).receive_init(m)
          for new_m in new_update_message_list:
            self.message_queue.put(dict({"type": "update"}, **new_m))


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
