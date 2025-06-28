import helpers

from lark import ParseTree, Token, Tree

def no_op(tree: ParseTree) -> list[ParseTree]:
    """
    For testing purposes.
    """
    print(tree.pretty())
    print(tree)
    return [tree]

# constraint/transition changing operators

def change_event(tree: ParseTree) -> list[ParseTree]:
    """
    Computes a list of mutations of the given TA such that for each mutation the event in one transition is changed.

    :param tree: AST of TA to be mutated
    :return: list of mutated ASTs
    """

    mutations = []

    # find events
    events = []
    for event in tree.find_data("event_declaration"):
        events.append(event.children[2])

    for edge in tree.find_data("edge_declaration"):
        # find suitable new events
        old_event = edge.children[8]
        new_event_options = events.copy()
        new_event_options.remove(old_event)

        for event in new_event_options:
            # exchange event
            altered_edge = helpers.exchange_node(edge, old_event, event)
            # exchange transition
            mutations.append(helpers.exchange_node(tree, edge, altered_edge))

    return mutations

def change_guard_cmp(tree: ParseTree) -> list[ParseTree]:
    """
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
    
    for edge in tree.find_data("edge_declaration"):
        for guard in edge.find_data("provided_attribute"):

            atomic_expressions = list(guard.find_data("predicate_expr"))
            atomic_expressions.extend(guard.find_data("clock_expr"))

            for expr in atomic_expressions:
                # check whether expression is a clock expression (lark might falsely classify a clock expression as a predicate expression, therefore additional checking is needed)
                is_clock_expr = False
                for clock_declaration in tree.find_data("clock_declaration"):
                    if(helpers.contains_child_node(expr, clock_declaration.children[4])):
                        is_clock_expr = True
                        break

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
                    altered_expr = helpers.exchange_node(expr, old_cmp_node, new_cmp_node)
                    altered_guard = helpers.exchange_node(guard, expr, altered_expr)
                    altered_edge = helpers.exchange_node(edge, guard, altered_guard)

                    mutations.append(helpers.exchange_node(tree, edge, altered_edge))
                
    return mutations

def decrease_or_increase_constraint_constant(tree: ParseTree, decrease_constant: bool) -> list[ParseTree]:
    """
    Computes a list of mutations of the given TA such that for each mutation the constant in one clock constraint is decreased or increased by one.

    :param tree: AST of TA to be mutated
    :param decrease_constant: Method decreases constant iff True, increases otherwise.
    :return: list of mutated ASTs
    """

    mutations = []

    def get_altered_expr_node(expr: ParseTree) -> ParseTree | None:
        # check whether first or second compared value is constant
        is_clock_expr = False
        for clock_declaration in tree.find_data("clock_declaration"):
            if(helpers.contains_child_node(expr.children[0], clock_declaration.children[4])):
                old_constant_node = expr.children[2]
                is_clock_expr = True
            elif(helpers.contains_child_node(expr.children[2], clock_declaration.children[4])):
                old_constant_node = expr.children[0]
                is_clock_expr = True
        # skip expression if it is no clock expression (lark might falsely classify a clock expression as a predicate expression, therefore additional checking is needed)
        if(not is_clock_expr):
            return None
        
        op_node = Tree(Token('RULE', 'op'), [Token('OP_SUB_TOK', '-')]) if decrease_constant else Tree(Token('RULE', 'op'), [Token('OP_ADD_TOK', '+')])
        one_node = Tree(Token('RULE', 'int_term'), [Token('SIGNED_INT', '1')])
        new_constant_node = Tree(Token('RULE', 'int_term'), [old_constant_node, op_node, one_node])

        return helpers.exchange_node(expr, old_constant_node, new_constant_node)
        
    # change guards
    for edge in tree.find_data("edge_declaration"):
        for guard in edge.find_data("provided_attribute"):
            
            atomic_expressions = list(guard.find_data("predicate_expr"))
            atomic_expressions.extend(guard.find_data("clock_expr"))

            for expr in atomic_expressions:
                altered_expr = get_altered_expr_node(expr)
                # skip expression if it is no clock expression (lark might falsely classify a clock expression as a predicate expression, therefore additional checking is needed)
                if(altered_expr == None):
                    continue
                
                altered_guard = helpers.exchange_node(guard, expr, altered_expr)
                altered_edge = helpers.exchange_node(edge, guard, altered_guard)

                mutations.append(helpers.exchange_node(tree, edge, altered_edge))

    # change invariants
    for location in tree.find_data("location_declaration"):
        for invariant in location.find_data("invariant_attribute"):

            atomic_expressions = list(invariant.find_data("predicate_expr"))
            atomic_expressions.extend(invariant.find_data("clock_expr"))

            for expr in atomic_expressions:
                altered_expr = get_altered_expr_node(expr)
                # skip expression if it is no clock expression (lark might falsely classify a clock expression as a predicate expression, therefore additional checking is needed)
                if(altered_expr == None):
                    continue
                
                altered_invariant = helpers.exchange_node(invariant, expr, altered_expr)
                altered_location = helpers.exchange_node(location, invariant, altered_invariant)

                mutations.append(helpers.exchange_node(tree, location, altered_location))

    return mutations

def invert_reset(tree: ParseTree) -> list[ParseTree]:
    """
    Computes a list of mutations of the given TA.
    For each mutation, the occurrence of one clock in the set of reset clocks of one guard is flipped.

    :param tree: AST of TA to be mutated
    :return: list of mutated ASTs
    """

    mutations = []

    # find clocks
    clocks = []
    for clock in tree.find_data("clock_declaration"):
        clocks.append(clock.children[4])

    for edge in tree.find_data("edge_declaration"):

        # add attribute list if edge declaration does not already have one
        if(10 > len(edge.children)):
            attributes = Tree(Token('RULE', 'attributes'), [Token('LEFT_BRACE_TOK', '{'), Token('RIGHT_BRACE_TOK', '}')])
            edge.children.append(attributes)

        non_reset_clocks = clocks.copy()

        # replace reset with nop if clock is reset by transition, add clock to non_reset_clocks otherwise
        for do_attribute in edge.find_data("do_attribute"):
            for assignment in do_attribute.find_pred(lambda t: t.data == "int_assignment" or t.data == "clock_assignment"):
                for clock in clocks:
                    if(isinstance(assignment.children[0], Tree) and clock == assignment.children[0].children[0]):
                        non_reset_clocks.remove(clock)

                        nop = Tree(Token('RULE', 'nop'), [Token('NOP_TOK', 'nop')])
                        altered_edge = helpers.exchange_node(edge, assignment, nop)
                        mutations.append(helpers.exchange_node(tree, edge, altered_edge))

        # add reset to attributes list if clock is not reset by transition
        for clock in non_reset_clocks:
            # define new reset
            new_reset = Tree(Token('RULE', 'do_attribute'), 
                        [Token('DO_TOK', 'do'), 
                        Token('COLON_TOK', ':'), 
                        Tree(Token('RULE', 'stmt'), 
                        [Tree(Token('RULE', 'clock_assignment'), 
                        [Tree(Token('RULE', 'clock_id'), [clock]), 
                        Token('ASSIGNMENT_TOK', '='), 
                        Tree(Token('RULE', 'int_term'), 
                        [Token('SIGNED_INT', '0')])])])])
            colon = Token('COLON_TOK', ':')

            # construct new edge
            altered_edge = edge.__deepcopy__(None)
            assert(isinstance(altered_edge.children[9], Tree))
            # add colon after new reset if attributes list was nonempty before
            if (altered_edge.children[9].children[1] != Token('RIGHT_BRACE_TOK', '}')):
                altered_edge.children[9].children.insert(1, colon)
            # add new reset
            altered_edge.children[9].children.insert(1, new_reset)
            mutations.append(helpers.exchange_node(tree, edge, altered_edge))

    return mutations

# structure changing operators

def add_location(tree: ParseTree) -> list[ParseTree]:
    """
    Computes a list of mutations of the given TA by adding a sink location.
    For each mutation, one transition of the TA is redirected to the new location.

    :param tree: AST of TA to be mutated
    :return: list of mutated ASTs
    """

    mutations = []

    for process in tree.find_data("process_declaration"):

        process_id = process.children[2]
        new_location_id = Tree(Token('RULE', 'id'), [Token('__ANON_0', 'new_loc')])
        # attribute list for new location is empty
        attributes = Tree(Token('RULE', 'attributes'), [Token('LEFT_BRACE_TOK', '{'), Token('RIGHT_BRACE_TOK', '}')])

        # define new location
        new_location = Tree(Token('RULE', 'location_declaration'), 
                       [Token('LOCATION_TOK', 'location'), 
                       Token('COLON_TOK', ':'), 
                       process_id, 
                       Token('COLON_TOK', ':'), 
                       new_location_id, 
                       attributes])
        
        # add new location 
        mutation = tree.__deepcopy__(None)
        new_location_index = mutation.children.index(process) + 1
        mutation.children.insert(new_location_index, Token('NEWLINE_TOK', '\n\n'))
        mutation.children.insert(new_location_index + 1, new_location)
        mutation.children.insert(new_location_index + 2, Token('NEWLINE_TOK', '\n'))

        # redirect transitions belonging to same process
        for edge in tree.find_pred(lambda t: t.data == "edge_declaration" and t.children[2] == process_id):

            altered_edge = edge.__deepcopy__(None)
            altered_edge.children[6] = new_location_id

            mutations.append(helpers.exchange_node(mutation, edge, altered_edge))

    return mutations

def add_transition(tree: ParseTree) -> list[ParseTree]:
    """
    Computes a list of mutations of the given TA.
    For each mutation, the first declared transition of the TA is cloned and its source and target location are changed to two different locations (both in the same process).

    :param tree: AST of TA to be mutated
    :return: list of mutated ASTs
    """

    mutations = []

    for process in tree.find_data("process_declaration"):

        process_id = process.children[2]

        # choose source and target location belonging to same process
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

                # skip this mutation if new edge is identical to cloned edge
                if(new_edge == next(tree.find_data("edge_declaration"))):
                    continue

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

    for edge in tree.find_data("edge_declaration"):

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
        for edge in tree.find_data("edge_declaration"):
            if(edge.children[2] == process_id and (edge.children[4] == location_id or edge.children[6] == location_id)):
                edges_to_be_removed.append(edge)

        # remove location and transitions belonging to it
        mutation = helpers.remove_node(tree, location)
        for edge in edges_to_be_removed:
            mutation = helpers.remove_node(mutation, edge)
        mutations.append(mutation)

    return mutations

def remove_transition(tree: ParseTree) -> list[ParseTree]:
    """
    Computes a list of mutations of the given TA such that for each mutation one transition is removed.

    :param tree: AST of TA to be mutated
    :return: list of mutated ASTs
    """

    mutations = []

    for edge in tree.find_data("edge_declaration"):
        # remove transition
        mutations.append(helpers.remove_node(tree, edge))

    return mutations