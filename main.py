import sys
import re
from cmd import Cmd
import queue
import yaml
import ipaddress

class AS_class_list:
  def __init__(self):
    self.class_list = {}
    self.ip_gen = IP_address_generator()

  def add_AS(self, as_number):
    if not as_number in self.class_list.keys():
      self.class_list[as_number] = AS_class(as_number, self.ip_gen.get_unique_address())
    else:
      print("Error: AS " + str(as_number) + " is already registered.", file=sys.stderr)

  def show_AS_list(self, param=""):

    tmp_param = []
    for p in param:
      tmp_param.append(p)

    try:
      tmp_param.remove("sort")
    except ValueError:
      pass
    try:
      tmp_param.remove("best")
    except ValueError:
      pass

    if len(tmp_param) >= 2:
      raise ASPAInputError
    elif len(tmp_param) == 1 and not re.fullmatch("((25[0-5]|2[0-4][0-9]|1[0-9][0-9]|[1-9]?[0-9])\.){3}(25[0-5]|2[0-4][0-9]|1[0-9][0-9]|[1-9]?[0-9])/[0-9][0-9]" , tmp_param[0]):
      raise ASPAInputError

    keys = list(self.class_list.keys())
    if "sort" in param:
      param.remove("sort")
      keys.sort()
    for k in keys:
      self.class_list[k].show_info(param)

  def get_AS(self, as_number):
    return self.class_list[as_number]

  def get_AS_list(self):
    return self.class_list

  def import_AS_list(self, import_list):

    self.class_list = {}
    for a in import_list:
      self.class_list[a["AS"]] = AS_class(a["AS"], a["network_address"])
      self.class_list[a["AS"]].policy = a["policy"]
      self.class_list[a["AS"]].routing_table.change_policy(a["policy"])
      self.class_list[a["AS"]].routing_table.table = a["routing_table"]


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

  def show_info(self, param):
    print("====================")
    print(f"AS NUMBER: {self.as_number}")
    print(f"network: {self.network_address}")
    print(f"policy: {self.policy}")

    only_best = False
    address = None
    try:
      if param.index("best") == 0:
        address = param[1]
      elif param.index("best") == 1:
        address = param[0]
      only_best = True
    except ValueError:
      if len(param) == 1:
        address = param[0]

    table = self.routing_table.get_table()
    addr_list = []
    for addr in table.keys():
      addr_list.append(ipaddress.ip_network(addr))
    addr_list.sort()

    print("routing table: (best path: > )")
    if address == None:
      for addr in addr_list:
        print(str(addr) + ":")
        for r in table[str(addr)]:
          path = r["path"]
          come_from = r["come_from"]
          LocPrf = r["LocPrf"]
          try:
            aspv = r["aspv"]
            if r["best_path"] == True:
              print(f"> path: {path}, LocPrf: {LocPrf}, come_from: {come_from}, aspv: {aspv}")
            elif only_best == True:
              continue
            else:
              print(f"  path: {path}, LocPrf: {LocPrf}, come_from: {come_from}, aspv: {aspv}")
          except KeyError:
            if r["best_path"] == True:
              print(f"> path: {path}, LocPrf: {LocPrf}, come_from: {come_from}")
            elif only_best == True:
              continue
            else:
              print(f"  path: {path}, LocPrf: {LocPrf}, come_from: {come_from}")
    else:
      print(str(address) + ":")
      try:
        for r in table[str(address)]:
          path = r["path"]
          come_from = r["come_from"]
          LocPrf = r["LocPrf"]
          try:
            aspv = r["aspv"]
            if r["best_path"] == True:
              print(f"> path: {path}, LocPrf: {LocPrf}, come_from: {come_from}, aspv: {aspv}")
            elif only_best == True:
              continue
            else:
              print(f"  path: {path}, LocPrf: {LocPrf}, come_from: {come_from}, aspv: {aspv}")
          except KeyError:
            if r["best_path"] == True:
              print(f"> path: {path}, LocPrf: {LocPrf}, come_from: {come_from}")
            elif only_best == True:
              continue
            else:
              print(f"  path: {path}, LocPrf: {LocPrf}, come_from: {come_from}")
      except KeyError:
        print("No-Path")
    print("====================")

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
    self.aspa_list = {}

  def change_policy(self, policy):
    self.policy = policy

  def set_public_aspa(self, public_aspa_list):
    self.aspa_list = public_aspa_list

  def verify_pair(self, customer_as, provider_as):
    try:
      candidate_provider_list = self.aspa_list[customer_as]
    except KeyError:
      return "Unknown"

    if provider_as in candidate_provider_list:
      return "Valid"
    else:
      return "Invalid"

  def aspv(self, route, neighbor_as):

    ###
    ### Referencing Internet-Draft draft-ietf-sidrops-aspa-verification-08
    ### https://www.ietf.org/archive/id/draft-ietf-sidrops-aspa-verification-08.txt
    ###

    p = route["path"]
    path_list = p.split("-")

    if re.fullmatch("customer|peer", route["come_from"]):

      if path_list[0] != neighbor_as:
        return "Invalid"

      try:
        index = -1
        semi_state = "Valid"
        while True:
          pair_check = self.verify_pair(path_list[index], path_list[index - 1])
          if pair_check == "Invalid":
            return "Invalid"
          elif pair_check == "Unknown":
            semi_state = "Unknown"
          index -= 1
      except IndexError:  # the end of checking
        pass

      return semi_state

    elif route["come_from"] == "provider":

      if path_list[0] != neighbor_as:
        return "Invalid"

      try:
        index = -1
        semi_state = "Valid"
        upflow_fragment = True
        while True:
          if upflow_fragment == True:
            pair_check = self.verify_pair(path_list[index], path_list[index - 1])
            if pair_check == "Invalid":
              upflow_fragment = False
            elif pair_check == "Unknown":
              semi_state = "Unknown"
            index -= 1
          elif upflow_fragment == False:
            # I-D version: It is thought to be wrong.
            # pair_check = self.verify_pair(path_list[index - 1], path_list[index])
            pair_check = self.verify_pair(path_list[index], path_list[index + 1])
            if pair_check == "Invalid":
              return "Invalid"
            elif pair_check == "Unknown":
              semi_state = "Unknown"
            index -= 1
      except IndexError:  # the end of checking
        pass

      return semi_state

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
      new_route["aspv"] = self.aspv(new_route, update_message["src"])

    try:
      new_route["best_path"] = False
      self.table[network].append(new_route)

      # select best path
      best = None
      for r in self.table[network]:
        if r["best_path"] == True:
          best = r
          break
      if best == None:
        raise BestPathNotExist

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
        elif p == "aspv":
          if new_route["aspv"] == "Invalid":
            return None

    except KeyError:
      if self.policy[0] == "aspv":
        if new_route["aspv"] == "Invalid":
          new_route["best_path"] = False
          self.table[network] = [new_route]
          return None
        else:
          new_route["best_path"] = True
          self.table[network] = [new_route]
          return {"path": path, "come_from": come_from, "network": network}
      else:
        new_route["best_path"] = True
        self.table[network] = [new_route]
        return {"path": path, "come_from": come_from, "network": network}

    except BestPathNotExist:
      if self.policy[0] == "aspv":
        if new_route["aspv"] == "Invalid":
          return None
        else:
          new_route["best_path"] = True
          return {"path": path, "come_from": come_from, "network": network}
      else:
        new_route["best_path"] = True
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

class BestPathNotExist(Exception):
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
      print("Usage: showAS [asn]", file=sys.stderr)

  def do_showASList(self, line):

    param = line.split()
    try:
      self.as_class_list.show_AS_list(param)
    except ASPAInputError:
      print("Usage: showASList [sort] [best] [address]", file=sys.stderr)

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
      print("Usage: addASPA [customer_asn] [provider_asns...]", file=sys.stderr)

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

  def do_export(self, line):

    try:
      if line == "":
        raise ASPAInputError
    except ASPAInputError:
      print("Usage: export [filename]", file=sys.stderr)
      return

    export_content = {}

    export_content["AS_list"] = []
    class_list = self.as_class_list.get_AS_list()
    for v in class_list.values():
      export_content["AS_list"].append({"AS": v.as_number, "network_address": v.network_address, "policy": v.policy, "routing_table": v.routing_table.get_table()})

    export_content["IP_gen_seed"] = self.as_class_list.ip_gen.index

    export_content["message"] = []
    tmp_queue = queue.Queue()
    while not self.message_queue.empty():
      q = self.message_queue.get()
      export_content["message"].append(q)
      tmp_queue.put(q)
    self.message_queue = tmp_queue

    export_content["connection"] = self.connection_list

    export_content["ASPA"] = self.public_aspa_list

    with open(line, mode="w") as f:
      yaml.dump(export_content, f)

  def do_import(self, line):

    try:
      if line == "":
        raise ASPAInputError
    except ASPAInputError:
      print("Usage: import [filename]", file=sys.stderr)
      return

    try:
      with open(line, mode="r") as f:
        import_content = yaml.safe_load(f)
    except FileNotFoundError as e:
      print("Error: No such file or directory: " + line, file=sys.stderr)
      return

    self.as_class_list.import_AS_list(import_content["AS_list"])

    self.as_class_list.ip_gen.index = import_content["IP_gen_seed"]

    self.message_queue = queue.Queue()
    for m in import_content["message"]:
      self.message_queue.put(m)

    self.connection_list = import_content["connection"]

    self.public_aspa_list = import_content["ASPA"]

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
