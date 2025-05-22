import argparse
import random

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

def apply_mutation(in_ta: str, out_ta: str, operator: str):
    """
    Applies mutation operator to given TA.

    :param in_ta: .txt or .tck file of TA to be mutated.
    :param out_ta: Path to .txt or .tck file for the mutated TA.
    :param operator: Mutation operator to be used.
    """ 
    if(operator == "remove_transition"):
        operators.remove_transition(in_ta, out_ta)
    else:
        raise ValueError("Unknown mutation operator.")

if "__main__" == __name__:

    # input
    parser = argparse.ArgumentParser()
    
    parser.add_argument(
        "--input_ta",
        type = str,
        required = True,
        help = "Timed automaton to be mutated. Must be .txt or .tck file in valid TChecker syntax."
    )
    parser.add_argument(
        "--output_file",
        type = str,
        required = True,
        help = "Path to output .txt file."
    )
    parser.add_argument(
        "--operator",
        type = str,
        required = True,
        help = "Mutation operator to be used.",
        choices = ["remove_transition"]
    )

    args = parser.parse_args()
    in_ta = args.input_ta
    out_ta = args.output_file

    # check for syntax errors
    if(not check_syntax(in_ta)):
        raise SyntaxError("Input TA has invalid syntax.")
    
    # compute new mutation if current one is bisimilar to input TA
    while(True):
        apply_mutation(in_ta, out_ta, args.operator)
        if(not check_bisimilarity(in_ta, out_ta)):
            break
