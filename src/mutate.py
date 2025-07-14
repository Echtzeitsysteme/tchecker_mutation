import operators
import transformers

import argparse
import os.path
import lark
import lark.reconstruct
import copy
import csv
# import random

# studs

def check_syntax(ta: str) -> bool:
    """
    Checks whether given TA has correct TChecker syntax.
    Not implemented yet.

    :param ta: .txt or .tck file of TA.
    :return: True iff given file has valid syntax.
    """ 
    return True

def check_reachability(ta: str) -> bool:
    """
    Checks reachability of the given TA.
    Not implemented yet.

    :param ta: .txt or .tck file of TA.
    :return: True iff reachability check was successful.
    :raises Error: if TA file is semantically faulty
    """ 
    return True

def check_bisimilarity(first: str, second: str) -> bool:
    """
    Checks whether given TA are bisimilar.
    Not implemented yet.

    :param first: .txt or .tck file of first TA
    :param second: .txt or .tck file of second TA
    :return: true iff given TA are bisimilar
    """ 
    # return random.choice([True, False])
    return False

def apply_mutation(ta_tree: lark.ParseTree, op: str, value: int) -> list[lark.ParseTree]:
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
        case "invert_sync_weakness":
            return operators.invert_sync_weakness(ta_tree)
        case "remove_sync":
            return operators.remove_sync(ta_tree)
        case "remove_sync_constraint":
            return operators.remove_sync_constraint(ta_tree)
        case _:
            raise ValueError("Unknown mutation operator.")

if "__main__" == __name__:

    op_choices = ["no_op", 
                  "all",
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
    in_ta = args.in_ta
    out_dir = args.out_dir
    op = args.op

    if(args.val):
        if(not(op == "decrease_constraint_constant" or op == "increase_constraint_constant" or op == "all")):
            raise Warning("Value argument is not needed for this operator and will be omitted.")
        value = args.val
    else:
        value = 1

    os.makedirs(out_dir, exist_ok=True)

    # assert that input TA file does not contain syntax errors
    assert(check_syntax(in_ta))

    # parsing input TA text file to AST
    ta_parser = lark.Lark.open("parsing/grammar.lark", __file__)
    ta_parser.options.maybe_placeholders = False
    with open(in_ta) as file:
        in_ta_tree = ta_parser.parse(file.read())

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
        for i, mutation in enumerate(mutations):

            file_name = f"{in_ta[:-4]}_mutation_{op}_{i}.tck"
            out_file = os.path.join(out_dir, file_name)

            # reconstructing TA text file from mutated AST
            reconstructor = lark.reconstruct.Reconstructor(ta_parser)
            out_ta = reconstructor.reconstruct(mutation)
            
            with open(out_file, "w") as file:
                file.write(out_ta)

            # assert that output TA file does not contain syntax errors
            assert(check_syntax(out_file))

            # delete mutation if it is semantically faulty
            try:
                check_reachability(out_file)
            except:
                os.remove(out_file)

            # check whether mutation is bisimilar to original
            is_bisimilar_to_original = check_bisimilarity(in_ta, out_file)

            # log bisimilarity of mutation
            csv_writer.writerow([file_name, is_bisimilar_to_original])

            # move mutation into seperate folder if it is bisimilar
            if(is_bisimilar_to_original):
                os.replace(out_file, os.path.join(bisimilar_mutations_folder, file_name))

    # compute mutations
    if (op == "all"):
        ops = op_choices.copy()
        ops.remove("no_op")
        ops.remove("all")

        for operator in ops:
            mutations = apply_mutation(copy.deepcopy(in_ta_tree), operator, value)
            write_mutations(mutations, operator)

    else:
        mutations = apply_mutation(copy.deepcopy(in_ta_tree), op, value)
        write_mutations(mutations, op)

    bisimilarity_log_file.close()
