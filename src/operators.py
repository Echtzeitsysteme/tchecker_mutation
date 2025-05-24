import lark
import random
from lark import Transformer

class Remove_Transition(Transformer):
    """
    Transformer that removes one randomly chosen transition from the given TA.
    """

    def __init__(self, tree: lark.ParseTree, visit_tokens: bool=True) -> None:
        """
        Chooses one edge declaration to be removed randomly from the tree.
        This method only chooses the declaration and does not change the tree in any way.

        :param tree: current node
        """
        self.__visit_tokens__ = visit_tokens

        number_of_edge_declarations_iter = tree.find_data("edge_declaration")
        number_of_edge_declarations = sum(1 for _ in number_of_edge_declarations_iter)

        self.__edge_to_be_removed__ = random.randint(1, number_of_edge_declarations)
        self.__edge_counter__ = 0

    @lark.visitors.v_args(tree=True)
    def edge_declaration(self, tree: lark.ParseTree):
        """
        Discards node iff it is the edge declaration chosen in start().

        :param self: transformer
        :param tree: current node
        :return: discard type iff current node is edge declaration to be removed, otherwise current node
        """
        self.__edge_counter__ += 1

        if(self.__edge_counter__ == self.__edge_to_be_removed__):
            return lark.visitors.Discard

        return tree