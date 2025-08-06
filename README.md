# TChecker Mutation

Enhanced mutation testing support for [TChecker](https://github.com/Echtzeitsysteme/tchecker/), the open source model checker for timed automata.

## Overview

Mutation testing is a powerful technique to generate test cases for your system.  
Potential errors in your system can be modelled by introducing controlled modifications (mutants) into timed automata models — such as altering clocks, guards and synchronisation.  
Test inputs that cause a mutant to behave differently from the original automaton can serve as a test case to find similar errors.  
TChecker provides efficient support for identifying such distinguishing test cases.

## Features

**TChecker Mutation** generates mutations by modifying a timed automaton's structure, clock constraints (guards and invariants), clock resets, event synchronisations and more.
In particular, the following operators for mutation generation are implemented:

- `no_op`
- `all`

### Attribute changing:

- `change_event` (from [1])
- `change_constraint_cmp` (inspired by [1])
- `change_constraint_clock`
- `decrease_constraint_constant` (from [2])
- `increase_constraint_constant` (from [2])
- `invert_committed_location` (from [3])
- `invert_reset` (from [1])
- `invert_urgent_location` (from [3])
- `negate_guard` (from [1])

### Structure changing:

- `add_location` (from [1])
- `add_transition` (from [2])
- `change_transition_source` (from [1])
- `change_transition_target` (from [1])
- `remove_location` (from [2])
- `remove_transition` (from [2])

### Synchronisation changing:

- `add_sync` (inspired by [3])
- `add_sync_constraint` (inspired by [3])
- `change_sync_event` (inspired by [3])
- `invert_sync_weakness` (inspired by [3])
- `remove_sync` (inspired by [3])
- `remove_sync_constraint` (inspired by [3])

For operator option `no_op`, one semantically identical TA is generated.  
For operator option `all`, all possible mutations for each implemented operator are generated (except for `no_op`).  
For operator options `decrease_constraint_constant`, `increase_constraint_constant` and `all`, an optional integer value to decrease/increase constants by can be specified. 
Default is 1.

## Prerequisites

To use **TChecker Mutation**, the following software is required:

- [lark](https://github.com/lark-parser/lark)
- [TChecker](https://github.com/Echtzeitsysteme/tchecker/)

## Usage

To generate mutations, run the following command:

```
$ python mutate.py --in_ta <input_tchecker_file> --out_dir <output_directory> --op <operator> [--val <int>]
```

For example:
```
$ python mutate.py --in_ta ad94.tck --out_dir out --op remove_location
```

The input file must be a .txt or .tck file in valid [TChecker syntax](https://github.com/ticktac-project/tchecker/wiki/TChecker-file-format).  
For a given timed automaton, every possible mutation is generated with the specified operator and written as a .tck file in the specified output directory.  
Mutations that are bisimilar to the original TA are written to a seperate directory `bisimilar_mutations` inside the output directory.  
Whether a mutation is bisimilar or not is logged in `bisimilarity_log.csv` in `bisimilar_mutations`.

Note: Output mutation files do not preserve comments of original TChecker file.

## Future Work

TChecker is not integrated into **TChecker Mutation** yet.
So far, **TChecker Mutation** does not check for bisimilarity by itself and treats all generated mutants as semantically correct and not bisimilar to the original timed automaton.

## Literature

1. [B. K. Aichernig, F. Lorber and D. Ničković. Time for Mutants - Model-Based Mutation Testing with Timed Automata (2013)](http://www.ist.tugraz.at/aichernig/publications/papers/tap13-time.pdf)
2. [D. Basile, M. H. ter Beek, S. Lazreg, M. Cordy, A. Legay. Static detection of equivalent mutants in real-time model-based mutation testing (2022)](https://link.springer.com/article/10.1007/s10664-022-10149-y)
3. [D. Cortés, J. Ortiz, D. Basile, J. Aranda, G. Perrouin, P. Schobbens. Time for Networks: Mutation Testing for Timed Automata
Networks (2024)](https://ieeexplore.ieee.org/document/10555774)