import copy

from lark import ParseTree, Token, Tree

# helper functions

def exchange_node(tree: ParseTree, old_node: ParseTree | Token, new_node: ParseTree | Token, occurrence_in_child_list: int = 1) -> ParseTree:
    """
    Exchanges old_node in given tree with new_node. By default, this method only exchanges the first occurrence of old_node in each node's child list.

    :param tree: tree to be altered
    :param old_node: node to be exchanged
    :param new_node: node old_node is to be exchanged with
    :param occurrence_in_child_list: If a node in the tree contains the old_node as a child multiple times, this parameter determines which one is exchanged. 
                                     For example, if occurrence_in_child_list == 2, only the second occurrence of the node in each child list is exchanged.
    :return: tree with old_node exchanged with new_node
    """

    if(not contains_child_node(tree, old_node)):
        raise ValueError("Tree does not contain node to be exchanged.")
    
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

    return exchange_node_helper(copy.deepcopy(tree), old_node, new_node, occurrence_in_child_list)

def remove_node(tree: ParseTree, node: ParseTree | Token, occurrence_in_child_list: int = 1) -> ParseTree:
    """
    Removes given node from given tree. By default, this method only removes the first occurrence of the node in each node's child list.

    :param tree: tree to be altered
    :param node: node to be removed
    :param occurrence_in_child_list: If a node in the tree contains the given node as a child multiple times, this parameter determines which one is removed. 
                                     For example, if occurrence_in_child_list == 2, the only second occurrence of the node in each child list is removed.
    :return: tree without given node
    """

    if(not contains_child_node(tree, node)):
        raise ValueError("Tree does not contain node to be removed.")
    
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

    return remove_node_helper(copy.deepcopy(tree), node, occurrence_in_child_list)

def contains_child_node(tree: ParseTree | Token, node: ParseTree | Token) -> bool:
    """
    Determines whether given tree contains given node.

    :param tree: tree to be searched
    :param node: node to search for
    :return: True iff tree contains node
    """

    if(tree == node):
        return True

    if(isinstance(tree, Tree)):
        for child in tree.children:
            if(contains_child_node(child, node)):
                return True
    return False

def is_clock_expr(tree: ParseTree, expr: ParseTree) -> bool:
    """
    Determines whether expression in given tree is a clock expression (contains a clock id).
    (Lark might falsely classify a clock expression as a predicate expression, therefore additional checking is needed.)

    :param tree: tree of TA the expression occurs in
    :param expr: expression to check
    :return: True iff expression is clock expression
    """

    for clock_declaration in tree.find_data("clock_declaration"):
        if(contains_child_node(expr, clock_declaration.children[4])):
            return True

    return False
