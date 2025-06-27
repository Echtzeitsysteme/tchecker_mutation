import argparse
import os.path
import lark
import lark.reconstruct

import helpers
import operators
import transformers

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
        choices = ["no_op", "change_guard_cmp", "add_transition", "change_transition_source", "change_transition_target", "remove_location", "remove_transition"]
    )

    args = parser.parse_args()
    in_ta = args.in_ta
    out_dir = args.out_dir
    op = args.op

    os.makedirs(out_dir, exist_ok=True)

    # assert that input TA file does not contain syntax errors
    assert(helpers.check_syntax(in_ta))

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
        assert(helpers.check_syntax(out_file))

        # delete mutation if it is bisimilar to original
        if(helpers.check_bisimilarity(in_ta, out_file)):
            os.remove(out_file)

        
    
