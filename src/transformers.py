import AST_tools

import copy
import lark

from lark import Transformer, ParseTree, Tree, Token

class SimplifyExpressions(Transformer):
    """
    Transforms each atomic expression of form a </<= b </<= c in the tree into a </<= b && b </<= c.
    """

    @lark.visitors.v_args(tree=True)
    def expr(self, tree: ParseTree) -> ParseTree:

        result = copy.deepcopy(tree)

        # find atomic expressions containing complex expressions
        def is_complex(tree: ParseTree):
            return 2 == sum(1 for _ in tree.scan_values(lambda t: t in ["<=", "<"]))
        
        is_complex_expression = lambda t: (t.data == "predicate_expr" or t.data == "clock_expr") and is_complex(t)
        complex_expressions = tree.find_pred(is_complex_expression)

        complex_expression = next(complex_expressions, None)
        i = 0
        while i < len(result.children):
            if complex_expression == None:
                return result
            if AST_tools.contains_child_node(result.children[i], complex_expression):

                # construct two simple expressions from complex expression
                first_new_atomic_expr = Tree(Token('RULE', 'atomic_expr'), 
                                             [Tree(Token('RULE', complex_expression.data), 
                                                   [complex_expression.children[0], 
                                                    complex_expression.children[1], 
                                                    complex_expression.children[2]])])
                second_new_atomic_expr = Tree(Token('RULE', 'atomic_expr'), 
                                              [Tree(Token('RULE', complex_expression.data), 
                                                    [complex_expression.children[2], 
                                                     complex_expression.children[3], 
                                                     complex_expression.children[4]])])

                # exchange complex expression with simple expressions
                result.children.pop(i)
                result.children.insert(i, first_new_atomic_expr)
                result.children.insert(i + 1, Token('LOGICAL_AND_TOK', '&&'))
                result.children.insert(i + 2, second_new_atomic_expr)

                complex_expression = next(complex_expressions, None)
                i += 3
            else:
                i += 1

        return result
    
class BreakUpEquals(Transformer):
    """
    Transforms each atomic expression of form `a == b` in the tree into `a <= b && a >= b`.
    """

    @lark.visitors.v_args(tree=True)
    def expr(self, tree: ParseTree) -> ParseTree:

        result = copy.deepcopy(tree)

        # find atomic expressions containing equals comparator
        is_expr_with_eq_cmp = lambda t: (t.data == "predicate_expr" or t.data == "clock_expr") and AST_tools.contains_child_node(t, Token("CMP_EQ_TOK", "=="))
        exprs_with_eq_cmp = tree.find_pred(is_expr_with_eq_cmp)

        expr_with_eq_cmp = next(exprs_with_eq_cmp, None)
        i = 0
        while i < len(result.children):
            if expr_with_eq_cmp == None:
                return result
            if AST_tools.contains_child_node(result.children[i], expr_with_eq_cmp):

                # construct two new expressions from expression with equals comparator
                first_new_atomic_expr = Tree(Token('RULE', 'atomic_expr'), 
                                             [Tree(Token('RULE', expr_with_eq_cmp.data), 
                                                   [expr_with_eq_cmp.children[0], 
                                                    Token("CMP_LEQ_TOK", "<="), 
                                                    expr_with_eq_cmp.children[2]])])
                second_new_atomic_expr = Tree(Token('RULE', 'atomic_expr'), 
                                              [Tree(Token('RULE', expr_with_eq_cmp.data), 
                                                    [expr_with_eq_cmp.children[0], 
                                                     Token("CMP_GEQ_TOK", ">="), 
                                                     expr_with_eq_cmp.children[2]])])

                # exchange expression with equals comparator with new expressions
                result.children.pop(i)
                result.children.insert(i, first_new_atomic_expr)
                result.children.insert(i + 1, Token('LOGICAL_AND_TOK', '&&'))
                result.children.insert(i + 2, second_new_atomic_expr)

                expr_with_eq_cmp = next(exprs_with_eq_cmp, None)
                i += 3
            else:
                i += 1

        return result

class combineGuards(Transformer):
    """
    Combines multiple guards of one transition into one by conjuction (in case one edge has more than one provided attribute).
    """

    @lark.visitors.v_args(tree=True)
    def edge_declaration(self, tree: ParseTree) -> ParseTree:

        result = copy.deepcopy(tree)

        guards = list(tree.find_data("provided_attribute"))
        old_guard = guards.pop(0)
        new_guard = copy.deepcopy(old_guard)

        for guard in guards:
            assert(isinstance(new_guard.children[2], Tree))
            new_guard.children[2].children.append(Token('LOGICAL_AND_TOK', '&&'))
            assert(isinstance(guard.children[2], Tree))
            new_guard.children[2].children.extend(guard.children[2].children)
            assert(isinstance(result.children[9], Tree))
            idx = result.children[9].children.index(guard)
            # remove preceding colon
            result.children[9].children.pop(idx - 1)
            # remove guard
            result.children[9].children.pop(idx - 1)

        return AST_tools.exchange_node(result, old_guard, new_guard)