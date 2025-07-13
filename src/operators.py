import AST_tools
import transformers

import sys
import copy

from lark import ParseTree, Token, Tree

def no_op(tree: ParseTree) -> list[ParseTree]:
    """
    For testing purposes.
    """
    print(tree.pretty())
    print(tree)
    return [tree]

# attribute changing operators

# cmp definitions
cmps = ["==", "<=", "<", ">=", ">"]
cmp_tokens = {
            "==": Token("CMP_EQ_TOK", "=="),
            "<=": Token("CMP_LEQ_TOK", "<="),
            "<": Token("CMP_LT_TOK", "<"),
            ">=": Token("CMP_GEQ_TOK", ">="),
            ">": Token("CMP_GT_TOK", ">")
            }

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
            altered_edge = AST_tools.exchange_node(edge, old_event, event)
            # exchange transition
            mutations.append(AST_tools.exchange_node(tree, edge, altered_edge))

    return mutations

def change_constraint_cmp(tree: ParseTree) -> list[ParseTree]:
    """
    Computes a list of mutations of the given TA such that for each mutation one comparator of one clock expression in one guard or invariant is changed.

    :param tree: AST of TA to be mutated
    :return: list of mutated ASTs
    """

    mutations = []
    
    edges_and_locations = list(tree.find_data("edge_declaration"))
    edges_and_locations.extend(tree.find_data("location_declaration"))

    for edge_or_location in edges_and_locations:
        if (edge_or_location.data == "edge_declaration"):
            constraints = edge_or_location.find_data("provided_attribute")
        else:
            constraints = edge_or_location.find_data("invariant_attribute")

        for constraint in constraints:

            atomic_expressions = list(constraint.find_data("predicate_expr"))
            atomic_expressions.extend(constraint.find_data("clock_expr"))
            clock_expressions = filter(lambda e: AST_tools.is_clock_expr(tree, e), atomic_expressions)

            for expr in clock_expressions:

                # new comparator can not be old comparator       
                old_cmp = next(expr.scan_values(lambda t: t in cmps))
                cmp_options = cmps.copy()
                cmp_options.remove(old_cmp)

                # define old comparator node
                old_cmp_node = cmp_tokens[old_cmp]

                for cmp in cmp_options:

                    # change node
                    altered_expr = AST_tools.exchange_node(expr, old_cmp_node, cmp_tokens[cmp])
                    altered_constraint = AST_tools.exchange_node(constraint, expr, altered_expr)
                    altered_edge_or_location = AST_tools.exchange_node(edge_or_location, constraint, altered_constraint)

                    mutations.append(AST_tools.exchange_node(tree, edge_or_location, altered_edge_or_location))
                
    return mutations

def decrease_or_increase_constraint_constant(tree: ParseTree, decrease_constant: bool, value: int) -> list[ParseTree]:
    """
    Computes a list of mutations of the given TA such that for each mutation the constant in one clock constraint is decreased or increased by given value.

    :param tree: AST of TA to be mutated
    :param decrease_constant: Method decreases constant iff True, increases otherwise.
    :param value: value to decrease/increase constant by
    :return: list of mutated ASTs
    """

    mutations = []
        
    edges_and_locations = list(tree.find_data("edge_declaration"))
    edges_and_locations.extend(tree.find_data("location_declaration"))

    for edge_or_location in edges_and_locations:
        if (edge_or_location.data == "edge_declaration"):
            constraints = edge_or_location.find_data("provided_attribute")
        else:
            constraints = edge_or_location.find_data("invariant_attribute")

        for constraint in constraints:
            
            atomic_expressions = list(constraint.find_data("predicate_expr"))
            atomic_expressions.extend(constraint.find_data("clock_expr"))
            clock_expressions = filter(lambda e: AST_tools.is_clock_expr(tree, e), atomic_expressions)

            for expr in clock_expressions:

                # check whether first or second compared value is constant
                for clock_declaration in tree.find_data("clock_declaration"):
                    if(AST_tools.contains_child_node(expr.children[0], clock_declaration.children[4])):
                        old_constant_node = expr.children[2]
                    elif(AST_tools.contains_child_node(expr.children[2], clock_declaration.children[4])):
                        old_constant_node = expr.children[0]

                # define new constant node
                op_node = Tree(Token('RULE', 'op'), [Token('OP_SUB_TOK', '-')]) if decrease_constant else Tree(Token('RULE', 'op'), [Token('OP_ADD_TOK', '+')])
                one_node = Tree(Token('RULE', 'int_term'), [Token('SIGNED_INT', value)])
                new_constant_node = Tree(Token('RULE', 'int_term'), [old_constant_node, op_node, one_node])

                # change node
                altered_expr = AST_tools.exchange_node(expr, old_constant_node, new_constant_node)
                altered_constraint = AST_tools.exchange_node(constraint, expr, altered_expr)
                altered_edge_or_location = AST_tools.exchange_node(edge_or_location, constraint, altered_constraint)

                mutations.append(AST_tools.exchange_node(tree, edge_or_location, altered_edge_or_location))

    return mutations

def invert_reset(tree: ParseTree) -> list[ParseTree]:
    """
    Computes a list of mutations of the given TA.
    For each mutation, the occurrence of one clock in the set of reset clocks of one guard is flipped.
    Only considers resets to 0.

    :param tree: AST of TA to be mutated
    :return: list of mutated ASTs
    """

    mutations = []

    # find clocks
    clocks = []
    for clock in tree.find_data("clock_declaration"):
        for i in range(int(str(clock.children[2]))):
            clock_id = clock.children[4]
            clock_node = Tree(Token('RULE', 'int_or_clock_id'), 
                         [clock_id, Token('LEFT_BRACKET_TOK', '['),
                          Tree(Token('RULE', 'int_term'), [Token('SIGNED_INT', i)]), 
                          Token('RIGHT_BRACKET_TOK', ']')])
            clocks.append(clock_node)

    for edge in tree.find_data("edge_declaration"):

        # add attribute list if edge declaration does not already have one
        if(10 > len(edge.children)):
            attributes = Tree(Token('RULE', 'attributes'), 
                              [Token('LEFT_BRACE_TOK', '{'), Token('RIGHT_BRACE_TOK', '}')])
            edge.children.append(attributes)

        non_reset_clocks = clocks.copy()

        # replace reset with nop if clock is reset by transition, add clock to non_reset_clocks otherwise
        for do_attribute in edge.find_data("do_attribute"):
            for assignment in do_attribute.find_pred(lambda t: t.data == "int_assignment" or t.data == "clock_assignment"):
                for clock in clocks:
                    # also consider resets of form x = 0 in addition to x[0] = 0
                    is_simple_clock_reset_of_same_clock = (isinstance(assignment.children[0], Tree) and len(assignment.children[0].children) == 1 and clock.children[0] == assignment.children[0].children[0])
                    if(clock == assignment.children[0] or is_simple_clock_reset_of_same_clock):
                        non_reset_clocks.remove(clock)

                        nop = Tree(Token('RULE', 'nop'), [Token('NOP_TOK', 'nop')])
                        altered_edge = AST_tools.exchange_node(edge, assignment, nop)
                        mutations.append(AST_tools.exchange_node(tree, edge, altered_edge))

        # add reset to attributes list if clock is not reset by transition
        for clock in non_reset_clocks:
            # define new reset
            new_reset = Tree(Token('RULE', 'do_attribute'),
                             [Token('DO_TOK', 'do'),
                              Token('COLON_TOK', ':'), 
                              Tree(Token('RULE', 'stmt'),
                                   [Tree(Token('RULE', 'clock_assignment'),
                                         [clock,
                                          Token('ASSIGNMENT_TOK', '='),
                                          Tree(Token('RULE', 'int_term'),
                                               [Token('SIGNED_INT', '0')])])])])
            colon = Token('COLON_TOK', ':')

            # define new edge
            altered_edge = copy.deepcopy(edge)
            assert(isinstance(altered_edge.children[9], Tree))
            # add colon after new reset if attributes list was nonempty before
            if (altered_edge.children[9].children[1] != Token('RIGHT_BRACE_TOK', '}')):
                altered_edge.children[9].children.insert(1, colon)
            # add new reset
            altered_edge.children[9].children.insert(1, new_reset)
            mutations.append(AST_tools.exchange_node(tree, edge, altered_edge))

    return mutations

def flip_urgent_or_committed_location(tree: ParseTree, flip_committed: bool) -> list[ParseTree]:
    """
    Computes a list of mutations of the given TA such that for each mutation the urgent or committed attribute of one location gets flipped (added if non-existent, removed if existent).

    :param tree: AST of TA to be mutated
    :param flip_committed: Method turns location committed iff True, urgent otherwise.
    :return: list of mutated ASTs
    """

    mutations = []

    if(flip_committed):
        attribute = Tree(Token('RULE', 'committed_attribute'),
                         [Token('COMMITTED_TOK', 'committed'), Token('COLON_TOK', ':')])
    else:
        attribute = Tree(Token('RULE', 'urgent_attribute'),
                         [Token('URGENT_TOK', 'urgent'), Token('COLON_TOK', ':')])    

    for location in tree.find_data("location_declaration"):
        # remove attribute if it already is urgent/committed
        if(AST_tools.contains_child_node(location, attribute)):
            altered_location = copy.deepcopy(location)

            assert(isinstance(altered_location.children[5], Tree))
            idx = altered_location.children[5].children.index(attribute)

            # remove preceeding and succeeding colons if necessary
            if(idx > 1):
                altered_location.children[5].children.pop(idx - 1)
                idx = idx - 1
            elif(idx < len(altered_location.children[5].children) - 2):
                altered_location.children[5].children.pop(idx + 1)

            # remove attribute
            altered_location = AST_tools.remove_node(altered_location, attribute)
            mutations.append(AST_tools.exchange_node(tree, location, altered_location))
            continue

        # add attribute list if location declaration does not already have one
        if(6 > len(location.children)):
            attributes = Tree(Token('RULE', 'attributes'), 
                              [Token('LEFT_BRACE_TOK', '{'), Token('RIGHT_BRACE_TOK', '}')])
            location.children.append(attributes)

        colon = Token('COLON_TOK', ':')

        # define new location
        altered_location = copy.deepcopy(location)
        assert(isinstance(altered_location.children[5], Tree))
        # add colon after new attribute if attributes list was nonempty before
        if (altered_location.children[5].children[1] != Token('RIGHT_BRACE_TOK', '}')):
            altered_location.children[5].children.insert(1, colon)
        # add new attribute
        altered_location.children[5].children.insert(1, attribute)
        mutations.append(AST_tools.exchange_node(tree, location, altered_location))

    return mutations

def negate_guard(tree: ParseTree) -> list[ParseTree]:
    """
    Computes a list of mutations of the given TA such that for each mutation one transition is removed.

    :param tree: AST of TA to be mutated
    :return: list of mutated ASTs
    """

    # transform equals comparator before negation since neq comparator is not allowed in clock expressions
    transformed_tree = transformers.BreakUpEquals().transform(copy.deepcopy(tree))

    mutations = []

    for edge in transformed_tree.find_data("edge_declaration"):
        for guard in edge.find_data("provided_attribute"):

            atomic_expressions = list(guard.find_data("predicate_expr"))
            atomic_expressions.extend(guard.find_data("clock_expr"))

            clock_expressions = list(filter(lambda e: AST_tools.is_clock_expr(transformed_tree, e), atomic_expressions))
            if(len(clock_expressions) == 0):
                continue

            # find int term expressions since they are not negated by operator
            int_term_expressions = list(filter(lambda e: (not AST_tools.is_clock_expr(transformed_tree, e)), atomic_expressions))
            # find atomic expressions that consist of a single int term since they are not negated by operator either
            is_single_int_term = lambda e: isinstance(e, Tree) and 0 == len(list(e.scan_values(lambda t: t in cmps)))
            single_int_terms = filter(is_single_int_term, guard.children[2].children)
            
            # define non-negated part of guard with int term expressions and single int terms
            int_term_part_of_guard = []
            for int_term in int_term_expressions:
                int_term_part_of_guard.append(Token('LOGICAL_AND_TOK', '&&'))
                int_term_part_of_guard.append(Tree(Token('RULE', 'atomic_expr'), [int_term]))
            for int_term in single_int_terms:
                int_term_part_of_guard.append(Token('LOGICAL_AND_TOK', '&&'))
                int_term_part_of_guard.append(int_term)

            # remove original transition
            mutation = AST_tools.remove_node(transformed_tree, edge)

            for expr in clock_expressions:
                
                def negate_expr(expr: ParseTree) -> ParseTree:
                    old_cmp = next(expr.scan_values(lambda t: t in cmps))

                    match old_cmp:
                        case "<=":
                            return AST_tools.exchange_node(expr, cmp_tokens[old_cmp], Token("CMP_GEQ_TOK", ">"))
                        case "<":
                            return AST_tools.exchange_node(expr, cmp_tokens[old_cmp], Token("CMP_GEQ_TOK", ">="))
                        case ">=":
                            return AST_tools.exchange_node(expr, cmp_tokens[old_cmp], Token("CMP_GEQ_TOK", "<"))
                        case ">":
                            return AST_tools.exchange_node(expr, cmp_tokens[old_cmp], Token("CMP_GEQ_TOK", "<="))
                        # there should be no equals comparators left after transformation
                        case _: 
                            raise ValueError(f"Unknown cmp {old_cmp}")
                
                # concatenate negated and non-negated part of guard
                all_atomic_expressions = []
                all_atomic_expressions.append(Tree(Token('RULE', 'atomic_expr'), [negate_expr(expr)]))
                all_atomic_expressions.extend(int_term_part_of_guard)
                
                # define new guard
                new_guard = Tree(Token('RULE', 'provided_attribute'),
                                 [Token('PROVIDED_TOK', 'provided'),
                                  Token('COLON_TOK', ':'),
                                  Tree(Token('RULE', 'expr'), all_atomic_expressions)])

                # exchange node                
                new_edge = AST_tools.exchange_node(edge, guard, new_guard)
                mutation.children.append(Token('NEWLINE_TOK', '\n\n'))
                mutation.children.append(new_edge)      
            
            mutations.append(mutation)

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

    # find fresh location id non-existent in original TA
    new_location_id = Tree(Token('RULE', 'id'), [Token('__ANON_0', 'new_loc')])
    for i in range(sys.maxsize):
        if(not AST_tools.contains_child_node(tree, new_location_id)):
            break
        new_location_id = Tree(Token('RULE', 'id'), [Token('__ANON_0', f'new_loc_{i}')])

    for process in tree.find_data("process_declaration"):

        process_id = process.children[2]
        # attribute list for new location is empty
        attributes = Tree(Token('RULE', 'attributes'), 
                          [Token('LEFT_BRACE_TOK', '{'), Token('RIGHT_BRACE_TOK', '}')])

        # define new location
        new_location = Tree(Token('RULE', 'location_declaration'),
                            [Token('LOCATION_TOK', 'location'),
                             Token('COLON_TOK', ':'), 
                             process_id, 
                             Token('COLON_TOK', ':'), 
                             new_location_id, 
                             attributes])
        
        # add new location 
        mutation = copy.deepcopy(tree)
        new_location_index = mutation.children.index(process) + 1
        mutation.children.insert(new_location_index, Token('NEWLINE_TOK', '\n\n'))
        mutation.children.insert(new_location_index + 1, new_location)
        mutation.children.insert(new_location_index + 2, Token('NEWLINE_TOK', '\n'))

        # redirect transitions belonging to same process
        for edge in tree.find_pred(lambda t: t.data == "edge_declaration" and t.children[2] == process_id):

            altered_edge = copy.deepcopy(edge)
            altered_edge.children[6] = new_location_id

            mutations.append(AST_tools.exchange_node(mutation, edge, altered_edge))

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
                new_edge = copy.deepcopy(next(tree.find_data("edge_declaration")))
                
                # exchange source and target location
                new_edge.children[2] = process_id
                new_edge.children[4] = source_location
                new_edge.children[6] = target_location

                # skip this mutation if new edge is identical to cloned edge
                if(new_edge == next(tree.find_data("edge_declaration"))):
                    continue

                # add transition    
                mutation = copy.deepcopy(tree)
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
            altered_edge = AST_tools.exchange_node(edge, old_location, location, occurrence)
            mutations.append(AST_tools.exchange_node(tree, edge, altered_edge))

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
        if AST_tools.contains_child_node(location, initial_attribute):
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
        mutation = AST_tools.remove_node(tree, location)
        for edge in edges_to_be_removed:
            mutation = AST_tools.remove_node(mutation, edge)
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
        mutations.append(AST_tools.remove_node(tree, edge))

    return mutations

# sync changing operators

def remove_sync(tree: ParseTree) -> list[ParseTree]:
    """
    Computes a list of mutations of the given TA such that for each mutation one synchronisation is removed.

    :param tree: AST of TA to be mutated
    :return: list of mutated ASTs
    """

    mutations = []

    for sync in tree.find_data("sync_declaration"):
        # remove sync
        mutations.append(AST_tools.remove_node(tree, sync))

    return mutations