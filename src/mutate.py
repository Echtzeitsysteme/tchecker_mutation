import argparse
import random
import lark
import lark.reconstruct

import operators

def check_syntax(ta: str) -> bool:
    """
    Checks whether given TA has correct TChecker syntax.
    Not implemented yet.

    :param ta: .txt or .tck file of TA.
    :return: True iff given file has valid syntax.
    """ 
    return True

def check_bisimilarity(first: str, second: str) -> bool:
    """
    Checks whether given TA are bisimilar.
    Not implemented yet.

    :param first: .txt or .tck file of first TA
    :param second: .txt or .tck file of secon TA
    :return: true iff given TA are bisimilar
    """ 
    return False
    return random.choice([True, False])

def apply_mutation(ta_tree: lark.ParseTree, op: str) -> lark.ParseTree:
    """
    Applies mutation operator to given TA.

    :param ta_tree: AST of TA to be mutated
    :param op: mutation operator to be used
    """ 

    # print tree for debugging
    # print(ta_tree.pretty())

    # mutating AST
    match op:
        case "no_op":
            # for testing purposes
            return operators.no_op(ta_tree)
        case "change_guard_cmp":
            return operators.change_guard_cmp(ta_tree)
        case "remove_location":
            return operators.remove_location(ta_tree)
        case "remove_transition":
            return operators.remove_transition(ta_tree)
        case _:
            raise ValueError("Unknown mutation operator.")
        
    # print tree for debugging
    # print(ta_tree.pretty())

if "__main__" == __name__:

    # input
    parser = argparse.ArgumentParser()
    
    parser.add_argument(
        "--in_ta",
        type = str,
        required = True,
        help = "Timed automaton to be mutated. Must be .txt or .tck file in valid TChecker syntax."
    )
    parser.add_argument(
        "--out_ta",
        type = str,
        required = True,
        help = "Path to output .txt file for mutated TA."
    )
    parser.add_argument(
        "--op",
        type = str,
        required = True,
        help = "Mutation operator to be used.",
        choices = ["no_op", "change_guard_cmp", "remove_location", "remove_transition"]
    )

    args = parser.parse_args()
    in_ta = args.in_ta
    out_ta = args.out_ta

    # assert that input TA file does not contain syntax errors
    assert(check_syntax(in_ta))

    # parsing input TA text file to AST
    parser = lark.Lark.open("parsing/grammar.lark", __file__)
    parser.options.maybe_placeholders = False
    in_ta_tree = parser.parse(open(in_ta).read())

    # compute new mutation if current one is bisimilar to input TA
    while(True):
        out_ta_tree = apply_mutation(in_ta_tree, args.op)

        # reconstructing TA text file from mutated AST
        reconstructor = lark.reconstruct.Reconstructor(parser)
        out_ta_str = reconstructor.reconstruct(out_ta_tree)
        open(out_ta, "wt+").write(out_ta_str)

        if(not check_bisimilarity(in_ta, out_ta)):
            break

    # assert that output TA file does not contain syntax errors
    assert(check_syntax(out_ta))
    
