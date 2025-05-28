import lark
import random
import typing

from lark import ParseTree, Tree, Token

def no_op(tree: ParseTree) -> ParseTree:
    """
    For testung purposes.
    """
    return tree

# constraint changing operators

def change_guard_cmp(tree: ParseTree) -> ParseTree:
    """
    Changes one comparator in a randomly chosen guard from the given TA.

    :param tree: AST of TA to be mutated
    :return: mutated TA AST
    """

    cmps = ["==", "<=", "<", ">=", ">", "!="]

    # find node to be changed
    guard_to_be_altered = choose_random_node_of_type(tree, "provided_attribute")
    atomic_expr_to_be_altered = choose_random_node_of_type(guard_to_be_altered, "atomic_expr")
    is_simple_atomic_expr = (1 == sum(1 for _ in atomic_expr_to_be_altered.scan_values(lambda t: t in cmps)))

    # check whether chosen atomic expression is a clock or int expression
    is_clock_expr = False
    id_nodes_in_atomic_expr = list(atomic_expr_to_be_altered.find_data("id"))
    for clock_declaration in tree.find_data("clock_declaration"):
        if(clock_declaration.children[4] in id_nodes_in_atomic_expr):
            is_clock_expr = True
    
    # cmp definitions
    less_cmps = ["<=", "<"]
    cmp_token_names = {
                "!=": "CMP_NEQ_TOK",
                "==": "CMP_EQ_TOK",
                "<=": "CMP_LEQ_TOK",
                "<": "CMP_LT_TOK",
                ">=": "CMP_GEQ_TOK",
                ">": "CMP_GT_TOK"
                }
    
    # change subtree of guard
    # atomic expression with one comparator
    if(is_simple_atomic_expr):

        # randomly choose new comparator
        cmp_options = cmps
        if(is_clock_expr):
            cmp_options.remove("!=")

        old_cmp = next(atomic_expr_to_be_altered.scan_values(lambda t: t in cmp_options))
        cmp_options.remove(old_cmp)
        new_cmp = random.choice(cmp_options)

        # define old and new comparator node
        old_cmp_node = Token(cmp_token_names[old_cmp], old_cmp)
        new_cmp_node = Token(cmp_token_names[new_cmp], new_cmp)

        # change comparator node
        altered_atomic_expr = exchange_node(atomic_expr_to_be_altered, old_cmp_node, new_cmp_node)
        
    # atomic expression with two comparators
    else:

        # randomly choose new comparator
        cmp_options = less_cmps
        cmps_in_expr = atomic_expr_to_be_altered.scan_values(lambda t: t in cmp_options)
        first_cmp = next(cmps_in_expr)
        second_cmp = next(cmps_in_expr)

        # randomly choose whether first or second comparator in expression is changed
        change_second_cmp = random.choice([True, False])
        old_cmp = second_cmp if change_second_cmp else first_cmp
        
        cmp_options.remove(old_cmp)
        new_cmp = cmp_options[0]

        # define old and new comparator node
        old_cmp_node = Token(cmp_token_names[old_cmp], old_cmp)
        new_cmp_node = Token(cmp_token_names[new_cmp], new_cmp)

        # change comparator node
        cmp_occurrence = 2 if change_second_cmp and first_cmp == second_cmp else 1
        altered_atomic_expr = exchange_node(atomic_expr_to_be_altered, old_cmp_node, new_cmp_node, cmp_occurrence)

    # change atomic expression node
    altered_guard = exchange_node(guard_to_be_altered, atomic_expr_to_be_altered, altered_atomic_expr)
    
    # change guard node
    return exchange_node(tree.copy(), guard_to_be_altered, altered_guard)
 
# structure changing operators

def remove_location(tree: ParseTree) -> ParseTree:
    """
    Removes one randomly chosen location from the given TA.

    :param tree: AST of TA to be mutated
    :return: mutated TA AST
    """

    # choose location to be removed
    suitable_locations = list(tree.find_data("location_declaration"))
    initial_attribute = next(tree.find_data("initial_attribute"))

    for location in suitable_locations:
        if contains_child_node(location, initial_attribute):
            suitable_locations.remove(location)

    location_to_be_removed = random.choice(suitable_locations)
    process_id = location_to_be_removed.children[2]
    location_id = location_to_be_removed.children[4]

    # find all transitions going into or out of chosen location
    edges_to_be_removed = []
    for edge in list(tree.find_data("edge_declaration")):
        if(edge.children[2] == process_id and (edge.children[4] == location_id or edge.children[6] == location_id)):
            edges_to_be_removed.append(edge)

    # remove location and transitions belonging to it
    result = tree.copy()
    remove_node(result, location_to_be_removed)
    for edge in edges_to_be_removed:
        remove_node(result, edge)

    return result

def remove_transition(tree: ParseTree) -> ParseTree:
    """
    Removes one randomly chosen transition from the given TA.

    :param tree: AST of TA to be mutated
    :return: mutated TA AST
    """

    edge_to_be_removed = choose_random_node_of_type(tree, "edge_declaration")
    return remove_node(tree.copy(), edge_to_be_removed)
    
# other operators

###

# helper functions

def exchange_node(tree: ParseTree, old_node, new_node, occurrence_in_child_list: int = 1) -> ParseTree:
    """
    Exchanges old_node in given tree with new_node. By default, this method only exchanges the first occurrence of old_node in each node's child list.

    :param tree: tree to be altered
    :param old_node: node to be exchanged
    :param new_node: node old_node is to be exchanged with
    :param occurrence_in_child_list: If a node in the tree contains the old_node as a child multiple times, this parameter determines which one is exchanged. 
                                     For example, if occurrence_in_child_list == 2, only the second occurrence of the node in each child list is exchanged.
    :returns: tree with old_node exchanged with new_node
    """

    if(not contains_child_node(tree, old_node)):
        raise ValueError("Tree does not contain node to be exchanged.")
    
    return exchange_node_helper(tree.copy(), old_node, new_node, occurrence_in_child_list)

def exchange_node_helper(tree: ParseTree, old_node, new_node, occurrence_in_child_list) -> ParseTree:
    
    # old_node is direct child node of tree
    if(occurrence_in_child_list <= tree.children.count(old_node)):
        occurrences_so_far = 0

        for i in range(len(tree.children)):
            if(tree.children[i] == old_node):
                occurrences_so_far += 1
                if(occurrences_so_far == occurrence_in_child_list):
                    tree.children[i] = new_node
    
    # given node is no direct child node of tree
    else:
        new_children = []

        for child in tree.children:
            if(isinstance(child, Token)):
                new_children.append(child)
            else:
                new_children.append(exchange_node_helper(child, old_node, new_node, occurrence_in_child_list))

        tree.set(tree.data, new_children)
    
    return tree

def remove_node(tree: ParseTree, node, occurrence_in_child_list: int = 1) -> ParseTree:
    """
    Removes given node from given tree. By default, this method only removes the first occurrence of the node in each node's child list.

    :param tree: tree to be altered
    :param node: node to be removed
    :param occurrence_in_child_list: If a node in the tree contains the given node as a child multiple times, this parameter determines which one is removed. 
                                     For example, if occurrence_in_child_list == 2, the only second occurrence of the node in each child list is removed.
    :returns: tree without given node
    """

    if(not contains_child_node(tree, node)):
        raise ValueError("Tree does not contain node to be removed.")
    
    return remove_node_helper(tree.copy(), node, occurrence_in_child_list)

def remove_node_helper(tree: ParseTree, node, occurrence_in_child_list) -> ParseTree:

    # given node is direct child node of tree
    if(occurrence_in_child_list <= tree.children.count(node)):
        occurrences_so_far = 0

        for i in range(len(tree.children)):
            if(tree.children[i] == node):
                occurrences_so_far += 1
                if(occurrences_so_far == occurrence_in_child_list):
                    idx = i

        tree.children.pop(idx)
    
    # given node is no direct child node of tree
    else:
        new_children = []

        for child in tree.children:
            if(isinstance(child, Token)):
                new_children.append(child)
            else:
                new_children.append(remove_node_helper(child, node, occurrence_in_child_list))

        tree.set(tree.data, new_children)
    
    return tree

def contains_child_node(tree, node) -> bool:
    """
    Determines whether given tree contains given node.
    """

    if(tree == node):
        return True
    
    if(isinstance(tree, Tree)):
        for child in tree.children:
            if(contains_child_node(child, node)):
                return True
    return False

def choose_random_node_of_type(tree: ParseTree, type: str) -> ParseTree:
    """
    Selects and returns a random node of given type in the given tree.

    :param tree: tree to be searched
    :param type: type of node to be returned
    :returns: random node of given type in the given tree
    """

    options = list(tree.find_data(type))

    if(0 == len(options)):
        raise ValueError("Tree does not contain node of given type.")
    
    return random.choice(options)
