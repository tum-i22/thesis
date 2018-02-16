import networkx as nx
# from clang.cindex import Index
import json
import sys, os
import copy
from anytree import Node, RenderTree, Resolver
from anytree.dotexport import RenderTreeGraph
from networkx.readwrite import json_graph
import glob
#from generate_separate_unit import find_func_node
from pycparser import c_parser, c_ast, parse_file

def find_func_node(node, func_name):
    ch = [c for c in node.get_children()]
    kinds = [c.kind for c in ch]
    if node.kind==CursorKind.FUNCTION_DECL and node.spelling==func_name and str(node.location.file).endswith('.c') and (CursorKind.COMPOUND_STMT in kinds): # Don't look at the header files or just declarations, but full definitions
        return node
    else:
        ch = [c for c in node.get_children()]
        if ch==[]:
            return None
        for c in ch:
            func_node = find_func_node(c, func_name)
            if func_node:
                return func_node

    return None

# Find a specific node by name
def find_node(data, node_label):
    for node in data["nodes"]:
        if "label" in node:
            if node_label in node["label"]:
                return node["id"]


# Find a specific label by node
def find_label(node_id):
    for node in data["nodes"]:
        if "id" in node:
            if node_id in node["id"]:
                if "label" in node:
                    return node["label"]
                else:
                    return node["id"]


# Tested
# Generate tree of the callgraph
def generate_tree(entry_node, root, visited=None):
    if visited is None:
        visited = set()
    for link in data["links"]:
        if entry_node in link["source"]:
            key = hash(entry_node + link["source"] + link["target"])
            if key not in visited:
                visited.add(key)
                name = find_label(link["target"])
                new_node = Node(name, parent=root)
                generate_tree(link["target"], new_node, visited)
    return root


# Tested
# The degree of a node is defined as the number of its neighboring edges
def node_degree(node):
    visited = set()
    counter_out = 0
    counter_in = 0
    for link in data["links"]:
        key = hash(link["source"] + link["target"])
        if key not in visited:
            if node in link["source"]:
                counter_out += 1
            if node in link["target"]:
                counter_in += 1
            visited.add(key)
    return counter_out, counter_in, counter_out + counter_in


# Looks for the shortest path to the requested node
# Have the root be the node, and average the distance to its children nodes
def node_path_length(tree, node_name):
    resolver = Resolver('name')
    total = 0
    children_number = 0
    start = '*'
    for i in range(tree.height):
        node = resolver.glob(tree, start + node_name)
        if node:
            node[0].parent = None
            result = get_all_children(node[0], total, children_number, True)
            total += result[0]
            children_number += result[1]
        else:
            start += '/*'
    if children_number != 0:
        total = total / children_number
    return total


# Looks for the shortest path to the requested node
def get_all_children(node, total, children_number, isRoot=False):
    for child in node.children:
        if child.children:
            result = get_all_children(child, total, children_number)
            total += result[0]
            children_number += result[1]
        else:
            total += child.depth
            children_number += 1
    if isRoot:
        return total, children_number
    else:
        return total, children_number


# Tested
# For a node u, the clustering coefficient c(u) represents the likelihood that any two neighbors of u are connected.
# Step 1: Get list, L, of all connected (sources or targets, anything) nodes to "node". 
# Step 2: For all pairs (a, b) of nodes in L:
#   Step 2a: If a!=b and a and b are connected (a->b or b->a), then add to clustering coefficient
def clustering_coefficient(list, degree):
    visited = set()
    triangles = 0
    ru = ((degree ** 2) - degree) / 2
    for related_node in list:
        for link in data["links"]:
            key = hash(related_node + link["source"] + link["target"])
            if key not in visited:
                if (related_node in link["source"]) and (link["target"] in list) and (link["source"] != link["target"]):
                    visited.add(key)
                    triangles += 1
    return triangles / ru if ru != 0 else 0


# Tested
def generate_connected_list(requested_node):
    list_nodes = []
    for link in data["links"]:
        if requested_node in link["source"]:
            list_nodes.append(link['target'])
        if requested_node in link["target"]:
            list_nodes.append(link['source'])
    set_nodes = list(set(list_nodes))
    return set_nodes


# Tested
# Distance from the node to the entry node.
def distance_to_interface(tree, node_name):
    resolver = Resolver('name')
    start = '*'
    for i in range(tree.height):
        node = resolver.glob(tree, start + node_name)
        if node != []:
            depth = node[0].depth
            return depth
        else:
            if node_name == '{external node}':
                return 0
            else:
                start += '/*'
    # When a node is not connected
    return 999

file_to_ast = {}

class FuncDefVisitor(c_ast.NodeVisitor):
    def __init__(self):
        self.inside_attributes = {}

    def lines_of_code(self, node):
        return len(node.body.block_items)

    def n_pointer_params(self, node):
        n=0
        for p in node.decl.type.args.params:
            if type(p.type) is c_ast.PtrDecl:
                n += 1
        return n

    def visit_FuncDef(self, node):
        self.inside_attributes[node.decl.name] = [self.lines_of_code(node), self.n_pointer_params(node)]

# FuncDefVisitor.visit() will always traverse the entire ast
# Therefore, call this function only once for every new file that is seen
def inside_function_attributes(file_name):
    """
    index = Index.create()
    tu = index.parse(file_name)
    if not tu:
        parser.error("unable to load input")
    
    func_node = find_func_node(tu.cursor, node_name)
    
    if func_node:
        func_node_length = func_node.extent.end.line - func_node.extent.start.line + 1
    else:
        print("Couldn't find the function node using clang.cindex.\nSetting length to 0")
        func_node_length = 0
    """

    func_node_length = 0
    ast = parse_file(file_name, use_cpp=True, cpp_args=r'-I/home/ognawala/build/pycparser/utils/fake_libc_include')

    v = FuncDefVisitor()
    v.visit(ast)
    file_to_ast[file_name] = v.inside_attributes

# Print results out.
def generate_json(node_id):
    requested_node = node_id
    connected_list = generate_connected_list(requested_node)
    disposable_tree = copy.deepcopy(tree)

    degree = node_degree(requested_node)
    macke_results = macke_attributes(node_name)

    results_json[node_name] = {"faulty": False, "node_degree": degree,
                               "distance_to_interface": distance_to_interface(disposable_tree, node_name),
                               "node_path_length": node_path_length(disposable_tree, node_name),
                               "clustering_coefficient": clustering_coefficient(connected_list, degree[2]),
                               "macke_vulnerabilities_found": macke_results[0],
                               "macke_bug_chain_length": macke_results[1],
                               "vulnerable_file": macke_results[2],
                               "vulnerable_instruction": macke_results[3], 
                               "vulnerable_instruction_text": macke_results[4]}
    
    if (macke_results[2]!=""):
        if macke_results[2] not in file_to_ast.keys():
            inside_function_attributes(macke_results[2])
        inside_attributes = file_to_ast[macke_results[2]][node_name.strip("{}")]
    else:
        inside_attributes = [0, 0]
    
    results_json[node_name]["function_length"] = inside_attributes[0]
    results_json[node_name]["n_pointer_args"] = inside_attributes[1]

    for cvss3_entry in cvss3_data:
        if node_name in cvss3_entry:
            results_json[node_name]["faulty"] = True
            results_json[node_name]["cvss3"] = cvss3_data[node_name]
            results_json[node_name]["macke_vulnerabilities_found"] = macke_results[0]
            results_json[node_name]["macke_bug_chain_length"] = macke_results[1]
            results_json[node_name]["vulnerable_instruction"] = macke_results[2]


def find_bug_chain_length(child_function, klee_json_data, bug_chain_length):
    caller_list = []
    for key, value in sorted(klee_json_data.items()):
        if value["phase"]==2:
            if '{' + value['callee'] + '}' == child_function:
                caller_list.append('{' + value['caller'] + '}')
    max_bug_chain_length = bug_chain_length
    if caller_list:
        for caller in caller_list:
            bug_chain_length_new = find_bug_chain_length(caller, klee_json_data, bug_chain_length+1)

            if bug_chain_length_new > max_bug_chain_length:
                max_bug_chain_length = bug_chain_length_new
    return max_bug_chain_length

# Read the instruction text from the file given the line number
def read_instruction_from_file(source_file, line_nu):
    if not os.path.isfile(source_file):
        return ""

    source = open(source_file, "r")

    for i, line in enumerate(source):
        if i==line_nu-1:
            return line.strip()

# Read a single error description file
def find_func_in_err_description(e, func_name):
    err_file = open(e, "r")

    line = " "
    for line in err_file:
        if "Stack:" in line:
            break

    if "Stack" not in line: # No call stack in the error description
        return "", 0, " "

    for line in err_file:
        if func_name in line:
            break

    if func_name not in line:
        return "", 0, " "

    line_nu = int(line.split(":")[-1].strip())

    source_file_base = line.split(":")[0].split("/")[-1].strip()
    line_text = read_instruction_from_file(source_root+"/"+source_file_base, line_nu)

    return source_root+"/"+source_file_base, line_nu, line_text

# Where is the function on the call stack?
def get_function_line(func_name, klee_out):
    err_descriptions = glob.glob(klee_out + "/test*.*.err")
    line_file = ""
    line_nu = 0
    line_text = ""

    if err_descriptions==[]:
        print("Strangely, found no error descriptions in "+klee_out)
        return line_file, line_nu, line_text
    
    ptr_err_descriptions = [p for p in err_descriptions if "ptr.err" in p]
    if ptr_err_descriptions:
        for p in ptr_err_descriptions:
            line_file, line_nu, line_text = find_func_in_err_description(p, func_name)
            if not line_nu==0:
                break
    
    if line_nu==0: # Didn't find the function in any ptr.err files. Trying with other err files
        for e in err_descriptions:
            line_file, line_nu, line_text = find_func_in_err_description(e, func_name)
            if not line_nu==0:
                break

    return line_file, line_nu, line_text

# Get line number of the vulnerable instruction from .err file
def get_vulnerable_instruction_line(json_node):
    klee_directory = sys.argv[1].rsplit('/', 1)[0] + "/klee/"
    
    # Which phase was the error found in?
    phase = int(json_node["phase"])

    # Where are the klee test cases stored?
    klee_out = klee_directory + json_node["folder"].rsplit('/', 1)[1]

    if phase==1: # Get function name directly
        return get_function_line(json_node["function"], klee_out)
    elif phase==2: # Get function name of caller
        return get_function_line(json_node["caller"], klee_out)
    
    return "", 0, ""

# Count number of vulnerabilities in a function
def get_n_vulnerabilities(klee_json_data, node_name):
    function_count_dict = [0, 0] # First index counts unique phase 1 bugs, second index counts unique phase 2 bugs

    once_skipped = False
    
    # We have to run two separate loops to make sure that phase 1 bugs are all read before phase 2 bugs
    for key, value in sorted(klee_json_data.items()):
        if "function" in value: # Phase 1 vulnerability: Add always
            if '{' + value["function"] + '}' == node_name:
                function_count_dict[0] += 1

    for key, value in sorted(klee_json_data.items()):
        if value["phase"]==2: # Phase 2 vulnerability: Add based on whether any other vulnerabilities have been added before or not
            if '{' + value["caller"] + '}' == node_name:
                if function_count_dict[0]==0: # If the same bug wasn't counted in phase 1
                    function_count_dict[1] += 1
                else: # If this bug has already been seen in phase 1
                    if (function_count_dict[1]==0) and (not once_skipped): # Skip the first count, because we have already counted it once in phase 1
                        once_skipped = True
                    else:
                        function_count_dict[1] += 1

    return function_count_dict[0] + function_count_dict[1] # Return total unique vulnerabilities (phase 1 + phase 2)

# Macke functions
# Number of vulnerabilities inside the function
def macke_attributes(node_name):
    directory = sys.argv[1].rsplit('/', 1)[0]
    number_of_bugs_found = 0
    bug_chain_length = 0
    instr_file = ""
    instr_line = 0
    instr_text = "" 

    with open(directory + "/klee.json") as klee_json:
        klee_json_data = json.load(klee_json)
    for key, value in sorted(klee_json_data.items()):
        if (value["phase"]==1 and '{' + value["function"] + '}'==node_name) or (value["phase"]==2 and '{' + value["caller"] + '}'==node_name): # node is an error description
            bug_chain_length = find_bug_chain_length(node_name, klee_json_data, 1)
            instr_file, instr_line, instr_text = get_vulnerable_instruction_line(value)
            number_of_bugs_found = get_n_vulnerabilities(klee_json_data, node_name)
    return number_of_bugs_found, bug_chain_length, instr_file, instr_line, instr_text

# Generate JSON for the frontend
def front_end_json():
    nodes = []
    links = []
    for link in data["links"]:
        link["source"] = find_label(link["source"])
        link["target"] = find_label(link["target"])
        links.append(link)
    for node in data["nodes"]:
        if "label" in node:
            node["id"] = node["label"]
            del node["label"]
        node["data"] = results_json[node['id']]
        type = results_json[node['id']]['distance_to_interface'] * results_json[node['id']][
            'macke_vulnerabilities_found'] * results_json[node['id']]['macke_bug_chain_length'] * \
               results_json[node['id']]['node_degree'][2] * results_json[node['id']][
                   'clustering_coefficient'] if not results_json[node['id']]['faulty'] else 999
        if "shape" in node:
            del node["shape"]

        node["type"] = type
        nodes.append(node)
    formatted_json = {
        'nodes': nodes,
        'links': links,
    }
    with open(sys.argv[1] + '_frontend.json', 'w') as frontend_json:
        json.dump(formatted_json, frontend_json)

# Main
if len(sys.argv) < 2:
    sys.stderr.write("Syntax : python %s <dot_file> <cvss3 file (in json)> {location of source C files (default '.')} {entry point (default 'main')}\n" % sys.argv[0])
else:
    dot_graph = nx.drawing.nx_agraph.read_dot(sys.argv[1])
    data = json_graph.node_link_data(dot_graph)

    #What the heck is this part doing anyway?
    '''
    data['links'] = [
        {
            'source': data['nodes'][link['source']]['id'],
            'target': data['nodes'][link['target']]['id']
        } for link in data['links']]
    '''

    with open(sys.argv[2]) as cvss3_file:
        cvss3_data = json.load(cvss3_file)
    source_root = sys.argv[3] if len(sys.argv) > 3 else "."
    
    if(source_root.endswith(".c")):
        print("WARNING: Are you sure your source root is %s?\n         and not %s"%(source_root, os.path.dirname(source_root)))

    interface = sys.argv[4] if len(sys.argv) > 4 else "external node"
    entry_node = find_node(data, interface)
    root = Node(interface)
    tree = generate_tree(entry_node, root)
    results_json = {}
    # We don't need the rendering for now
    # RenderTreeGraph(tree).to_picture(sys.argv[1] + "_callgraph.png")

    # For testing purposes only -- Displays the current tree
    # for pre, fill, node in RenderTree(tree):
    #     print("%s%s" % (pre, node.name))

    for node in data["nodes"]:
        if "label" in node:
            node_name = node['label']
        else:
            node_name = node['id']
        generate_json(node['id'])

    with open(sys.argv[1] + '_node_attributes.json', 'w') as fp:
        json.dump(results_json, fp)

    # Prepare a JSON file to be used in our ReactJS front-end
    front_end_json()
    print('Done with:', sys.argv[1])
