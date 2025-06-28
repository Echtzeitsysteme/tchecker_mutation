import argparse
import os.path
import lark
import lark.reconstruct

import operators
import transformers

# studs

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

def apply_mutation(ta_tree: lark.ParseTree, op: str) -> list[lark.ParseTree]:
    """
    Applies mutation operator to given TA.

    :param ta_tree: AST of TA to be mutated
    :param op: mutation operator to be used
    :return: list of mutations
    """ 

    # mutating AST
    match op:
        case "no_op":
            # for testing purposes
            return operators.no_op(ta_tree)
        case "change_guard_cmp":
            return operators.change_guard_cmp(ta_tree)
        case "decrease_constraint_constant":
            return operators.decrease_or_increase_constraint_constant(ta_tree, decrease_constant = True)
        case "increase_constraint_constant":
            return operators.decrease_or_increase_constraint_constant(ta_tree, decrease_constant = False)
        case "invert_reset":
            return operators.invert_reset(ta_tree)
        case "add_location":
            return operators.add_location(ta_tree)
        case "add_transition":
            return operators.add_transition(ta_tree)
        case "change_transition_source":
            return operators.change_transition_source_or_target(ta_tree, change_source = True)
        case "change_transition_target":
            return operators.change_transition_source_or_target(ta_tree, change_source = False)
        case "remove_location":
            return operators.remove_location(ta_tree)
        case "remove_transition":
            return operators.remove_transition(ta_tree)
        case "change_event":
            return operators.change_event(ta_tree)
        case _:
            raise ValueError("Unknown mutation operator.")

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
        "--out_dir",
        type = str,
        required = True,
        help = "Path to output directory for mutated TA files."
    )
    parser.add_argument(
        "--op",
        type = str,
        required = True,
        help = "Mutation operator to be used.",
        choices = ["no_op", 
                   "change_guard_cmp", 
                   "decrease_constraint_constant",
                   "increase_constraint_constant",
                   "invert_reset",
                   "add_location", 
                   "add_transition", 
                   "change_transition_source", 
                   "change_transition_target", 
                   "remove_location", 
                   "remove_transition", 
                   "change_event"]
    )

    args = parser.parse_args()
    in_ta = args.in_ta
    out_dir = args.out_dir
    op = args.op

    os.makedirs(out_dir, exist_ok=True)

    # assert that input TA file does not contain syntax errors
    assert(check_syntax(in_ta))

    # parsing input TA text file to AST
    parser = lark.Lark.open("parsing/grammar.lark", __file__)
    parser.options.maybe_placeholders = False
    in_ta_tree = parser.parse(open(in_ta).read())

    # simplifying complex expressions in AST
    in_ta_tree = transformers.SimplifyExpressions().transform(in_ta_tree)

    # compute mutations
    mutations = apply_mutation(in_ta_tree.__deepcopy__(None), op)

    for i in range(len(mutations)):

        out_file = os.path.join(out_dir, f"{in_ta[:-4]}_mutation_{op}_{i}.tck")

        # reconstructing TA text file from mutated AST
        reconstructor = lark.reconstruct.Reconstructor(parser)
        out_ta = reconstructor.reconstruct(mutations[i])
        open(out_file, "wt+").write(out_ta)

        # assert that output TA file does not contain syntax errors
        assert(check_syntax(out_file))

        # delete mutation if it is bisimilar to original
        if(check_bisimilarity(in_ta, out_file)):
            os.remove(out_file)

        
    
