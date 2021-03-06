import networkx as nx
# from clang.cindex import Index
import json
import sys, os, time
import copy
from anytree import Node, RenderTree, Resolver
from anytree.dotexport import RenderTreeGraph
from networkx.readwrite import json_graph
import glob
import subprocess
#from generate_separate_unit import find_func_node
from pycparser import c_parser, c_ast, parse_file, preprocess_file, CParser

ALLOWED_FUNCTIONS = ["parse_string_node", "uint24_from_be", "copy_plist_data", "write_data", "write_raw_data", "xmlDictComputeFastKey", "xmlDictCreate", "xmlDictAddQString", "xmlDictAddString"]

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

def get_descendant_dist(current_node, current_dist):
    res = []

    connected = generate_connected_list(current_node, both_ways=False)
    for c in connected:
        res.append(1+current_dist)
        res.extend(get_descendant_dist(c, 1+current_dist))

    return res

# Not tested, but better than the obsolete version
def node_path_length(node_name):
    if ("plist" in sys.argv[1]) or ("xml" in sys.argv[1]):
        if node_name.strip("{}") not in ALLOWED_FUNCTIONS:
            return 0
    descendant_dist = get_descendant_dist(node_name, 0)
    total_desc_dist = 0

    for d in descendant_dist:
        total_desc_dist += d

    return total_desc_dist/len(descendant_dist) if len(descendant_dist)>0 else 0

# Looks for the shortest path to the requested node
# Have the root be the node, and average the distance to its children nodes
def obsolete_node_path_length(tree, node_name):
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
def clustering_coefficient(connected_list):
    visited = set()
    triangles = 0
    degree = len(connected_list)
    ru = ((degree ** 2) - degree) / 2

    """
    link = data["links"]
    for a in connected_list:
        a_connected = link["source"][a] + link["target"][a]
        for b in a_connected:
            if b==a:
                continue
            if (b in connected_list):
                triangles += 1
    
    """
    for related_node in connected_list:
        for link in data["links"]:
            if (related_node in link["source"]) and (link["target"] in connected_list) and (link["source"] != link["target"]):
                key = hash(related_node + link["source"] + link["target"])
                if key not in visited:
                    visited.add(key)
                    triangles += 1
    
    return triangles / ru if ru != 0 else 0


# Tested
def generate_connected_list(requested_node, both_ways=True):
    list_nodes = []
    for link in data["links"]:
        if requested_node in link["source"]:
            list_nodes.append(link['target'])
        if both_ways and requested_node in link["target"]:
            list_nodes.append(link['source'])
    set_nodes = list(set(list_nodes))
    return set_nodes

def find_dist(node_name, interface, cur_dist, closed):
    closed.append(interface)
    if cur_dist>=999:
        return cur_dist

    if node_name==interface:
        return cur_dist

    connected_list = generate_connected_list(interface, both_ways=False)
    
    min_dist = 999
    for c in connected_list:
        try:
            if c in closed:
                continue
            temp_dist = find_dist(node_name, c, cur_dist+1, closed)
            if temp_dist<min_dist:
                min_dist = temp_dist
        except RecursionError:
            return 999

    return min_dist

# Not tested, but better than obsolete version
def distance_to_interface(node_name, interface):
    #return 0
    if ("plist" in sys.argv[1]) or ("xml" in sys.argv[1]):
        print("In exceptional program: %s"%(sys.argv[1]))
        if node_name.strip("{}") not in ALLOWED_FUNCTIONS:
            return 999

    return find_dist(node_name, "{"+interface+"}", 0, [])

# Tested
# Distance from the node to the entry node.
def obs_distance_to_interface(tree, node_name):
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

    def n_ifs(self, node):
        n = 0
        for s in node.body.block_items:
            if type(s) is c_ast.If:
                n += 1

        return n

    def n_loops(self, node):
        n = 0
        for s in node.body.block_items:
            if (type(s) is c_ast.For) or (type(s) is c_ast.While):
                n += 1

        return n
                
    def lines_of_code(self, node):
        return len(node.body.block_items)

    def n_pointer_params(self, node):
        n=0
        for p in node.decl.type.args.params:
            if type(p.type) is c_ast.PtrDecl:
                n += 1
        return n

    def visit_FuncDef(self, node):
        self.inside_attributes[node.decl.name] = [self.lines_of_code(node), self.n_pointer_params(node), self.n_ifs(node), self.n_loops(node)]


# call opt LLVM pass
def function_internal_attributes(node_name, bitcode_path):
    res = []
    opt_pass_out = subprocess.check_output(["/home/ognawala/build/llvm/Release/bin/opt" ,"-load=/home/ognawala/macke-opt-llvm/bin/libMackeOpt.so",  "-functioninternalattributes",  "-functionname="+node_name, bitcode_path, "-o", "/dev/null"]).splitlines()
    
    for line in opt_pass_out:
        try:
            res.append(int(line.strip()))
        except ValueError:
            pass
    if not res:
        #to find which nodes are getting this
        print("No internal attributes for: %s"%(node_name))
        res = [0, 0, 0]
    return res

# Print results out.
def generate_json(node_name, bitcode, interface):
    #connected_list = generate_connected_list(node_name)
    disposable_tree = copy.deepcopy(tree)

    macke_results = macke_attributes(node_name)

    results_json[node_name] = {"faulty": False, "node_degree": node_degree(node_name),
                               "distance_to_interface": distance_to_interface(node_name, interface),
                               "node_path_length": node_path_length(node_name),
                               "clustering_coefficient": clustering_coefficient(generate_connected_list(node_name)),
                               "macke_vulnerabilities_found": macke_results[0],
                               "macke_bug_chain_length": macke_results[1],
                               "vulnerable_file": macke_results[2],
                               "vulnerable_instruction": macke_results[3], 
                               "vulnerable_instruction_text": macke_results[4]}
    
    
    """
    if (macke_results[2]!="" and os.path.isfile(macke_results[2])):
        if macke_results[2] not in file_to_ast.keys():
            inside_function_attributes(macke_results[2], include_path)
        inside_attributes = file_to_ast[macke_results[2]][node_name.strip("{}")]
    """
    inside_attributes = function_internal_attributes(node_name.strip("{}"), bitcode)
    """
    else:
        inside_attributes = [0, 0, 0]
    """
    #print("Function internal attributes:")
    #print(inside_attributes)
    results_json[node_name]["function_length"] = inside_attributes[0]
    results_json[node_name]["n_blocks"] = inside_attributes[1]
    results_json[node_name]["n_pointer_args"] = inside_attributes[2]
    #results_json[node_name]["n_pointer_args"] = inside_attributes[1]
    #results_json[node_name]["n_ifs"] = inside_attributes[2]
    #results_json[node_name]["n_loops"] = inside_attributes[3]

    for cvss3_entry in cvss3_data:
        if node_name==cvss3_entry:
            print("CVSS score found for: %s"%(node_name))
            results_json[node_name]["faulty"] = True
            results_json[node_name]["cvss3"] = cvss3_data[node_name]
            # Why are we setting macke bits again?
            """
            results_json[node_name]["macke_vulnerabilities_found"] = macke_results[0]
            results_json[node_name]["macke_bug_chain_length"] = macke_results[1]
            results_json[node_name]["vulnerable_instruction"] = macke_results[2]
            """
        elif node_name.strip("{}")==cvss3_entry:
            try:
                results_json[node_name]["faulty"] = True
                results_json[node_name]["cvss3"] = cvss3_data[node_name.strip("{}")]
            except KeyError:
                print("KeyError: " + node_name)
                print(cvss3_entry)
                print("Won't go on.")
                sys.exit()

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
    #line_text = read_instruction_from_file(source_root+"/"+source_file_base, line_nu)

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
            #line_file, line_nu, line_text = find_func_in_err_description(p, func_name)
            if not line_nu==0:
                break
    
    if line_nu==0: # Didn't find the function in any ptr.err files. Trying with other err files
        for e in err_descriptions:
            #line_file, line_nu, line_text = find_func_in_err_description(e, func_name)
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
if len(sys.argv) < 3: 
    sys.stderr.write("Syntax : python3 %s <dot_file> <cvss3 file (in json)> <output_folder> {entry point (default 'main')}\n" % sys.argv[0])
else:
    print("Not generating frontend JSON...")
    dot_graph = nx.drawing.nx_agraph.read_dot(sys.argv[1])
    data = json_graph.node_link_data(dot_graph)

    # Remove recursive calls
    for link in data["links"]:
        if link["source"] == link["target"]:
            print("Found recursive call in: %s"%(link["source"]))
            link["target"] = ""
    
    # In the list of edges replace source and target IDs with their names (function names)
    id_to_label = {}

    for node in data["nodes"]:
        try:
            id_to_label[node["id"]] = node["label"]
        except KeyError:
            print("No label found in: %s"%(node))
    for link in data["links"]:
        try:
            link["source"] = id_to_label[link["source"]]
            link["target"] = id_to_label[link["target"]]
        except KeyError:
            pass
    
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

    if (os.path.isdir(sys.argv[3])):
        out_dir = sys.argv[3]
    else:
        print("Output directory doesn't exist: %s"%(sys.argv[3]))
        sys.exit()

    interface = sys.argv[4] if len(sys.argv) > 5 else "external node"
    
    entry_node = find_node(data, interface)
    root = Node(interface)
    tree = generate_tree(entry_node, root)

    results_json = {}
    # We don't need the rendering for now
    # RenderTreeGraph(tree).to_picture(sys.argv[1] + "_callgraph.png")

    # For testing purposes only -- Displays the current tree
    # for pre, fill, node in RenderTree(tree):
    #     print("%s%s" % (pre, node.name))
    '''
    for node in data["nodes"]:
        print(node['label'])
    '''
    for node in data["nodes"]:
        
        if "label" in node:
            node_name = node['label']
        else:
            node_name = node['id']
        
        generate_json(node_name, os.path.dirname(sys.argv[1])+"/bitcode/program.bc", interface)

    node_attributes_dot = os.path.basename(sys.argv[1])
    with open(out_dir + "/" + node_attributes_dot + '.node_attributes.json', 'w') as fp:
        json.dump(results_json, fp)

    # Prepare a JSON file to be used in our ReactJS front-end
    #front_end_json()
    print('Done with:', sys.argv[1])
