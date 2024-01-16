import itertools
import os, csv, re, time
import networkx as nx
from google.colab import drive

def extend_and_replace_duplicates(input_arr, fill_values):
  input_set = set(input_arr)
  fill_set = set(fill_values)
  values_needed = len(fill_values) - len(input_set)
  output = input_arr + list(itertools.islice((fill_set - input_set), values_needed))
  output = list(itertools.islice(output, len(fill_values)))
  return output

def parse_data(file_path, parse_function):
  with open(file_path, 'r') as file:
    data = file.read()
  rows = data.strip().split('\n')[1:]
  rows = [row.split(',') for row in rows]
  
  return parse_function(rows)

def parse_groups(rows):
  groups = {}
  for row in rows:
    module = row[0]
    name = row[1]
    id = int(row[2])
    max_users = int(row[3])
    if module not in groups:
      groups[module] = []
    groups[module].append({'name': name, 'id': id, 'max_users': max_users})
  return groups

def parse_modules(rows):
  modules = set()
  for row in rows:
    modules.add(row[0])
  return modules

def parse_users(rows):
  parsed_rows = []
  for row in rows:
    timestamp, email, name, id, grade, *choices = row
    formatted_choices = {}
    for i, current_module in enumerate(modules):
      start = i * CHOICES_PER_MODULE
      end = start + CHOICES_PER_MODULE
      formatted_choices[current_module] = choices[start:end]

      fill_values = [group['name'] for group in groups[current_module]]
      unique_elements = {}
      result = extend_and_replace_duplicates(formatted_choices[current_module], fill_values)
      formatted_choices[current_module] = result

    parsed_rows.append({
      'name': name,
      'id': int(id),
      'email': email,
      'grade': int(grade),
      'choices': formatted_choices
    })
  return parsed_rows

def list_users(user_objects, modules):
  user_data = "name,id,"
  for current_module in sorted(modules):
    user_data += current_module + ','

  user_objects = sorted(user_objects, key=lambda u: u.name)

  for u in user_objects:
    user_data = user_data[:-1] + "\n"
    user_data += f"{u.name},{u.id},"
    for current_module in sorted(modules):
      if not u.group.get(current_module):
        continue
      user_data += f"{u.group[current_module].name},"
  
  if not os.path.exists(OUTPUT_DIR):
    os.mkdir(OUTPUT_DIR)
  with open(OUTPUT_DIR + "users.csv", "w") as file:
    file.write(user_data.strip()[:-1])
  return True

def list_groups(group_objects):
  for g in group_objects:
    user_data = ""
    for current_user in g.users:
      user_data += f"{current_user.name}, {current_user.id}\n"
    module_path = os.path.join(OUTPUT_DIR, g.module)
    os.makedirs(module_path, exist_ok=True)
    with open(os.path.join(module_path, f"{g.name}.csv"), "w") as file:
      file.write(user_data.strip())
  return True

def sort_users(users, groups):
  class User:
    def __init__(self, name, email, id, grade, choices):
      self.name = name
      self.email = email
      self.id = id
      self.grade = grade
      self.__choices = choices
      self.__group = {}
      
      for current_module in modules:
        self.__group[current_module] = None
    
    @property
    def group(self):
      return self.__group
    
    @property
    def choices(self):
      return self.__choices
    
    def set_group(self, group_class, module):
      self.__group[module] = group_class
  
  class Group:
    def __init__(self, name, id, max_users, module):
      self.name = name
      self.id = id
      self.grade = self.parse_range(name)
      self.max_users = max_users
      self.module = module
      self.__users = []
  
    @property
    def user_count(self):
      return len(self.__users)
  
    @property
    def users(self):
      return self.__users
  
    def add_user(self, user_class, module):
      self.__users.append(user_class)
      user_class.set_group(self, module)
  
    def parse_range(self, string):
      pattern = r'\b(\d+)(?:-(\d+))?\b'
      matches = re.findall(pattern, string)
      numbers = []
      for match in matches:
        if match[1]:
          start = int(match[0])
          end = int(match[1])
          numbers.extend(range(start, end + 1))
        else:
          numbers.append(int(match[0]))
      return numbers
  
  user_objects = [User(user['name'], user['email'], user['id'], user['grade'], user['choices']) for user in users]
  group_objects = [Group(group['name'], group['id'], group['max_users'], module) for module, groups in groups.items() for group in groups]
  
  for current_module in modules:
    G = nx.DiGraph()
    G.add_node('dest', demand=len(user_objects))

    module_group_objects = [group for group in group_objects if group.module == current_module]
    for user in user_objects:
      G.add_node(str(user.id), demand=-1)
      for i, group_name in enumerate(user.choices[current_module]):
        group_object = next((obj for obj in module_group_objects if obj.name == group_name), None)
        if group_object.grade != None and group_object.grade != [] and user.grade not in group_object.grade:
          cost = 100000
        else:
          cost = PREFERENCE_COST_MAP.get(i, -1)
        G.add_edge(str(user.id), group_name, capacity=1, weight=cost)

    for group in module_group_objects:
      G.add_edge(group.name, 'dest', capacity=group.max_users, weight=0)

    flowdict = nx.min_cost_flow(G)
  
    for user in user_objects:
      for group_name, flow in flowdict[str(user.id)].items():
        if flow:
          group_object = next((obj for obj in module_group_objects if obj.name == group_name), None)
          group_object.add_user(user, current_module)

    perfect_cost = PREFERENCE_COST_MAP.get(0, -1) * len(user_objects)
    total_cost = sum(flow * G[str(user.id)][group_name]['weight'] for user in user_objects for group_name, flow in flowdict[str(user.id)].items() if flow)

  return [user_objects, group_objects, total_cost, perfect_cost]

if __name__ == "__main__":
  CHOICES_PER_MODULE = 4

  # Change these to favour certain positions for best results
  PREFERENCE_COST_MAP = {
    0: -100,
    1: -50,
    2: -20,
    3: -10,
    4: 5,
    5: 10
  }
  INPUT_DIR = '/content/drive/My Drive/sorting_system/input/'
  OUTPUT_DIR = '/content/drive/My Drive/sorting_system/output/'
  
  drive.mount('/content/drive')

  groups = parse_data(INPUT_DIR + 'groups.csv', parse_groups)
  modules = parse_data(INPUT_DIR + 'groups.csv', parse_modules)
  users = parse_data(INPUT_DIR + 'users.csv', parse_users)

  start_time = time.time()
  sorted_users = sort_users(users, groups)
  
  print("Total cost:", sorted_users[2])
  print("(Maybe Impossible) Perfect Cost:", sorted_users[3])
  print("Finished! Total time taken: {:.2f}s".format((time.time() - start_time) ))

  list_users(sorted_users[0], modules)
  list_groups(sorted_users[1])

  drive.flush_and_unmount()
  print('All changes made in this colab session should now be visible in Drive.')
