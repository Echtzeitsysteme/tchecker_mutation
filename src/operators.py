import helpers

from lark import ParseTree, Token

def no_op(tree: ParseTree) -> list[ParseTree]:
    """
    For testing purposes.
    """
    return [tree]

# constraint changing operators

def change_guard_cmp(tree: ParseTree) -> list[ParseTree]:
    """
    Changes one comparator in a randomly chosen guard from the given TA.
    Computes a list of mutations of the given TA such that for each mutation one comparator in one guard is changed.

    :param tree: AST of TA to be mutated
    :return: list of mutated ASTs
    """

    mutations = []

    # cmp definitions
    cmps = ["==", "<=", "<", ">=", ">", "!="]
    cmp_token_names = {
                "!=": "CMP_NEQ_TOK",
                "==": "CMP_EQ_TOK",
                "<=": "CMP_LEQ_TOK",
                "<": "CMP_LT_TOK",
                ">=": "CMP_GEQ_TOK",
                ">": "CMP_GT_TOK"
                }
    
    # find transitions
    edges = list(tree.find_data("edge_declaration"))

    for edge in edges:
        # find guards
        guards = list(edge.find_data("provided_attribute"))

        for guard in guards:
            # find atomic expressions
            atomic_expressions = list(guard.find_data("atomic_expr"))

            for expr in atomic_expressions:
                # skip expression if it does not contain comparator (expression is an int term)
                if(0 == len(list(expr.find_data("predicate_expr"))) and 0 == len(list(expr.find_data("clock_expr")))):
                    continue

                # check whether expression is a clock or int expression
                is_clock_expr = False
                id_nodes_in_atomic_expr = list(expr.find_data("id"))
                for clock_declaration in tree.find_data("clock_declaration"):
                    if(clock_declaration.children[4] in id_nodes_in_atomic_expr):
                        is_clock_expr = True

                # if expression is clock expression, new comparator can not be !=
                cmp_options = cmps.copy()
                if(is_clock_expr):
                    cmp_options.remove("!=")

                # new comparator can not be old comparator
                old_cmp = next(expr.scan_values(lambda t: t in cmp_options))
                cmp_options.remove(old_cmp)

                # define old comparator node
                old_cmp_node = Token(cmp_token_names[old_cmp], old_cmp)

                for cmp in cmp_options:
                    # define new comparator node
                    new_cmp_node = Token(cmp_token_names[cmp], cmp)

                    # change node
                    altered_atomic_expr = helpers.exchange_node(expr, old_cmp_node, new_cmp_node)
                    altered_guard = helpers.exchange_node(guard, expr, altered_atomic_expr)
                    altered_edge = helpers.exchange_node(edge, guard, altered_guard)

                    mutation = helpers.exchange_node(tree, edge, altered_edge)
                    mutations.append(mutation)
                
    return mutations

# structure changing operators

def add_transition(tree: ParseTree) -> list[ParseTree]:
    """
    Computes a list of mutations of the given TA.
    For each mutation, the first declared transition of the TA is cloned and its source and target location are changed to two different locations (both in the same process).

    :param tree: AST of TA to be mutated
    :return: list of mutated ASTs
    """

    mutations = []

    # find processes
    processes = list(tree.find_data("process_declaration"))

    for process in processes:

        process_id = process.children[2]

        # choose source and target location belonging to chosen process
        locations = []
        for location in tree.find_data("location_declaration"):
            if(location.children[2] == process_id):
                locations.append(location.children[4]) 

        for source_location in locations:
            for target_location in locations:

                # find transition to be cloned (first transition)
                new_edge = next(tree.find_data("edge_declaration")).__deepcopy__(None)
                
                # exchange source and target location
                new_edge.children[2] = process_id
                new_edge.children[4] = source_location
                new_edge.children[6] = target_location

                # add transition    
                mutation = tree.__deepcopy__(None)
                mutation.children.append(Token('NEWLINE_TOK', '\n\n'))
                mutation.children.append(new_edge)

                mutations.append(mutation)

    return mutations

def change_transition_source_or_target(tree: ParseTree, change_source: bool) -> list[ParseTree]:
    """
    Computes a list of mutations of the given TA such that for each mutation the source or target location of one transition is changes to a different location in the same process.

    :param tree: AST of TA to be mutated
    :param change_source: Method changes source location of transition iff True, target location otherwise.
    :return: list of mutated ASTs
    """

    mutations = []

    # find transitions
    edges = list(tree.find_data("edge_declaration"))

    for edge in edges:

        process_id = edge.children[2]
        source_location_id = edge.children[4]
        target_location_id = edge.children[6]
        old_location = source_location_id if change_source else target_location_id

        occurrence = 2 if not change_source and source_location_id == target_location_id else 1

        # find new source or target location
        new_location_options = []
        for location in tree.find_data("location_declaration"):
            if(location.children[2] == process_id):
                new_location_options.append(location.children[4])
        new_location_options.remove(old_location)
            
        for location in new_location_options:
            # change transition
            altered_edge = helpers.exchange_node(edge, old_location, location, occurrence)
            mutations.append(helpers.exchange_node(tree, edge, altered_edge))

    return mutations

def remove_location(tree: ParseTree) -> list[ParseTree]:
    """
    Computes a list of mutations of the given TA such that for each mutation one location is removed.

    :param tree: AST of TA to be mutated
    :return: list of mutated ASTs
    """

    mutations = []

    # find non-initial locations
    locations = list(tree.find_data("location_declaration"))
    initial_attribute = next(tree.find_data("initial_attribute"))
    for location in locations:
        if helpers.contains_child_node(location, initial_attribute):
            locations.remove(location)

    for location in locations:
        process_id = location.children[2]
        location_id = location.children[4]

        # find all transitions going into or out of location
        edges_to_be_removed = []
        for edge in list(tree.find_data("edge_declaration")):
            if(edge.children[2] == process_id and (edge.children[4] == location_id or edge.children[6] == location_id)):
                edges_to_be_removed.append(edge)

        # remove location and transitions belonging to it
        mutation = helpers.remove_node(tree, location)
        for edge in edges_to_be_removed:
            helpers.remove_node(mutation, edge)
        mutations.append(mutation)

    return mutations

def remove_transition(tree: ParseTree) -> list[ParseTree]:
    """
    Computes a list of mutations of the given TA such that for each mutation one transition is removed.

    :param tree: AST of TA to be mutated
    :return: list of mutated ASTs
    """

    mutations = []

    # find transitions
    edges = list(tree.find_data("edge_declaration"))

    for edge in edges:
        mutation = helpers.remove_node(tree, edge)
        mutations.append(mutation)

    return mutations
    
# other operators

###