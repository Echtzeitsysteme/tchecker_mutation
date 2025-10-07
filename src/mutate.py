import operators
import transformers
from tcheckerpy.tools import tck_compare, tck_reach, tck_syntax

import argparse
import os.path
import lark
import lark.reconstruct
import csv

def check_syntax(ta: str) -> bool:
    """
    Checks whether given TA has correct TChecker syntax.

    :param ta: system declaration of TA as string
    :return: True iff given declaration has valid syntax
    """ 
    try:
        tck_syntax.check(ta)
        return True
    except:
        return False

def check_reachability(ta: str) -> bool:
    """
    Checks reachability of the given TA.

    :param ta: system declaration of TA as string
    :return: True iff reachability check was successful
    :raises Error: if TA file is semantically faulty
    """ 
    return tck_reach.reach(ta, tck_reach.Algorithm.REACH)[0]

def check_bisimilarity(first: str, second: str) -> bool:
    """
    Checks whether given TA are bisimilar.

    :param first: system declaration of first TA as string
    :param second: system declaration of second TA as string
    :return: true iff given TA are bisimilar
    """ 
    return tck_compare.compare(first, second)[0]

def apply_mutation(ta_tree: lark.ParseTree, op: str, value: int) -> list[lark.ParseTree]:
    """
    Applies mutation operator to given TA.

    :param ta_tree: AST of TA to be mutated
    :param op: mutation operator to be used
    :return: list of mutations
    """ 

    # mutating AST
    match op:
        case "change_event":
            return operators.change_event(ta_tree)
        case "change_constraint_cmp":
            return operators.change_constraint_cmp(ta_tree)
        case "change_constraint_clock":
            return operators.change_constraint_clock(ta_tree)
        case "decrease_constraint_constant":
            return operators.decrease_or_increase_constraint_constant(ta_tree, decrease_constant = True, value = value)
        case "increase_constraint_constant":
            return operators.decrease_or_increase_constraint_constant(ta_tree, decrease_constant = False, value = value)
        case "invert_committed_location":
            return operators.invert_urgent_or_committed_location(ta_tree, invert_committed = True)
        case "invert_reset":
            return operators.invert_reset(ta_tree)
        case "invert_urgent_location":
            return operators.invert_urgent_or_committed_location(ta_tree, invert_committed = False)
        case "negate_guard":
            return operators.negate_guard(ta_tree)
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
        case "add_sync":
            return operators.add_sync(ta_tree)
        case "add_sync_constraint":
            return operators.add_sync_constraint(ta_tree)
        case "change_sync_event":
            return operators.change_sync_event(ta_tree)
        case "invert_sync_weakness":
            return operators.invert_sync_weakness(ta_tree)
        case "remove_sync":
            return operators.remove_sync(ta_tree)
        case "remove_sync_constraint":
            return operators.remove_sync_constraint(ta_tree)
        case _:
            raise ValueError("Unknown mutation operator.")

if "__main__" == __name__:

    op_choices = ["all",
                  "change_event",
                  "change_constraint_cmp", 
                  "change_constraint_clock", 
                  "decrease_constraint_constant",
                  "increase_constraint_constant",
                  "invert_committed_location",
                  "invert_reset",
                  "invert_urgent_location",
                  "negate_guard",
                  "add_location", 
                  "add_transition", 
                  "change_transition_source", 
                  "change_transition_target", 
                  "remove_location", 
                  "remove_transition",
                  "add_sync",
                  "add_sync_constraint",
                  "change_sync_event",
                  "invert_sync_weakness",
                  "remove_sync",
                  "remove_sync_constraint"]

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
        choices = op_choices
    )
    parser.add_argument(
        "--val",
        type = str,
        required = False,
        help = "Value to decrease/increase constants by (for operators decrease_constraint_constant and increase_constraint_constant). Must be positive integer. Default is 1." 
    )

    args = parser.parse_args()
    in_file = args.in_ta
    out_dir = args.out_dir
    op = args.op

    if(args.val):
        if(not(op == "decrease_constraint_constant" or op == "increase_constraint_constant" or op == "all")):
            raise Warning("Value argument is not needed for this operator and will be omitted.")
        value = args.val
    else:
        value = 1

    os.makedirs(out_dir, exist_ok=True)
    
    with open(in_file) as file:
        in_ta = file.read()

    # assert that input TA file does not contain syntax errors
    assert(check_syntax(in_ta))

    # parsing input TA text file to AST
    ta_parser = lark.Lark.open("parsing/grammar.lark", __file__)
    ta_parser.options.maybe_placeholders = False
    in_ta_tree = ta_parser.parse(in_ta)

    # simplifying complex expressions in AST
    in_ta_tree = transformers.SimplifyExpressions().transform(in_ta_tree)

    # create folder for bisimilar mutations
    bisimilar_mutations_folder = os.path.join(out_dir, "bisimilar_mutations")
    if not os.path.isdir(bisimilar_mutations_folder):
        os.makedirs(bisimilar_mutations_folder)

    # create log file for bisimilar mutations
    bisimilarity_log_file = open(os.path.join(bisimilar_mutations_folder, "bisimilarity_log.csv"), mode='w+', newline='')
    csv_writer = csv.writer(bisimilarity_log_file)
    csv_writer.writerow(["mutation", "result of bisimilarity check"])

    def write_mutations(mutations: list[lark.ParseTree], op: str) -> None:

        original_file_name = os.path.basename(in_file)[:-4]

        i = 0
        for mutation in mutations:
              
            file_name = f"{original_file_name}_mutation_{op}_{i}.tck"
            i = i + 1
            out_file = os.path.join(out_dir, file_name)

            # reconstructing TA text file from mutated AST
            reconstructor = lark.reconstruct.Reconstructor(ta_parser)
            out_ta = reconstructor.reconstruct(mutation)
            
            with open(out_file, "w") as file:
                file.write(out_ta)

            # assert that output TA file does not contain syntax errors
            assert(check_syntax(out_ta))

            # delete mutation if it is semantically faulty
            try:
                check_reachability(out_ta)
            except:
                os.remove(out_file)
                i = i - 1
                continue

            # check whether mutation is bisimilar to original
            is_bisimilar_to_original = check_bisimilarity(in_ta, out_ta)

            # log bisimilarity of mutation
            csv_writer.writerow([file_name, is_bisimilar_to_original])

            # move mutation into seperate folder if it is bisimilar
            if(is_bisimilar_to_original):
                os.replace(out_file, os.path.join(bisimilar_mutations_folder, file_name))

    # compute mutations
    if (op == "all"):
        ops = op_choices.copy()
        ops.remove("all")

        for operator in ops:
            mutations = apply_mutation(in_ta_tree, operator, value)
            write_mutations(mutations, operator)

    else:
        mutations = apply_mutation(in_ta_tree, op, value)
        write_mutations(mutations, op)

    bisimilarity_log_file.close()
