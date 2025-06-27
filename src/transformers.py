import lark

import helpers

from lark import Transformer, ParseTree, Tree, Token

class SimplifyExpressions(Transformer):
    """
    Transforms each atomic expression of form `a </<= b </<= c` in the tree into `a </<= b && b </<= c`.
    """

    @lark.visitors.v_args(tree=True)
    def expr(self, tree: ParseTree) -> ParseTree:

        result = tree.__deepcopy__(None)

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
            if helpers.contains_child_node(result.children[i], complex_expression):

                # construct two simple expressions from complex expression
                first_new_atomic_expr = Tree(Token('RULE', 'atomic_expr'), [Tree(Token('RULE', complex_expression.data), [complex_expression.children[0], complex_expression.children[1], complex_expression.children[2]])])
                second_new_atomic_expr = Tree(Token('RULE', 'atomic_expr'), [Tree(Token('RULE', complex_expression.data), [complex_expression.children[2], complex_expression.children[3], complex_expression.children[4]])])

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