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

    :param first: .txt or .tck file of first TA.
    :param second: .txt or .tck file of secon TA.
    :return: True iff given TA are bisimilar.
    """ 
    return random.choice([True, False])

def apply_mutation(in_ta: str, out_ta: str, op: str):
    """
    Applies mutation operator to given TA.

    :param in_ta: .txt or .tck file of TA to be mutated.
    :param out_ta: Path to .txt or .tck file for the mutated TA.
    :param op: Mutation operator to be used.
    """ 

    # parsing input TA text file to AST
    parser = lark.Lark.open("parsing/grammar.lark", __file__)
    parser.options.maybe_placeholders = False
    in_tree = parser.parse(open(in_ta).read())

    # mutating AST
    if(op == "remove_transition"):
        out_tree = operators.remove_transition(in_tree)
    else:
        raise ValueError("Unknown mutation operator.")
    
    # reconstructing TA text file from mutated AST
    reconstructor = lark.reconstruct.Reconstructor(parser)
    out_ta_str = reconstructor.reconstruct(out_tree)
    open(out_ta, "wt").write(out_ta_str)

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
        choices = ["remove_transition"]
    )

    args = parser.parse_args()
    in_ta = args.in_ta
    out_ta = args.out_ta

    # check for syntax errors in input TA file
    if(not check_syntax(in_ta)):
        raise SyntaxError("Input TA has invalid syntax.")
    
    # compute new mutation if current one is bisimilar to input TA
    while(True):
        apply_mutation(in_ta, out_ta, args.op)
        if(not check_bisimilarity(in_ta, out_ta)):
            break

    # check for syntax errors in output TA file
    if(not check_syntax(out_ta)):
        raise SyntaxError("Computed mutation has invalid syntax.")
    
