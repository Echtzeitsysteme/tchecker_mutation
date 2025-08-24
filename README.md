# TChecker Mutation

Enhanced mutation testing support for [TChecker](https://github.com/Echtzeitsysteme/tchecker/), the open source model checker for timed automata and timed automata networks.

## Overview

Mutation testing is a powerful technique to generate test cases for your system.  
Potential errors in your system can be modelled by introducing controlled modifications (mutants) into timed automata models — such as altering clocks, guards and synchronisation.  
Test inputs that cause a mutant to behave differently from the original automaton can serve as a test case to find similar errors.  
**TChecker Mutation** provides efficient support for identifying such distinguishing test cases based on TChecker.

## Features

**TChecker Mutation** generates mutations of timed automata networks by modifying their structure, clock constraints (guards and invariants), clock resets, event synchronisations and more.
In particular, the following operators for mutation generation are implemented:

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

For operator option `all`, all possible mutations for each implemented operator are generated.  
For operator options `decrease_constraint_constant`, `increase_constraint_constant` and `all`, an optional integer value to decrease/increase constants by can be specified. 
Default is 1.

## Prerequisites

Before using **TChecker Mutation**, install the required dependencies:

```bash
pip install -r requirements.txt 
```

You will also need to build the TChecker shared library.
Follow the instructions in the [TChecker documentation](https://github.com/ticktac-project/tchecker/wiki/Installation-of-TChecker) to build the library and set the `LIBTCHECKER_ENABLE_SHARED` option to `ON` during the CMake configuration step:

```bash
cmake ../tchecker -DCMAKE_BUILD_TYPE=Release -DCMAKE_INSTALL_PREFIX=/path/to/install -DLIBTCHECKER_ENABLE_SHARED=ON
```

Now copy the TChecker shared library binary to the `tchecker` directory of the project:

```bash
cp path_to_tchecker_installation/lib/libtchecker.so ./tchecker/libtchecker.so
```

## Usage

To generate mutations, run the following command:

```bash
python mutate.py --in_ta <input_tchecker_file> --out_dir <output_directory> --op <operator> [--val <int>]
```

For example:
```bash
python mutate.py --in_ta ad94.tck --out_dir out --op remove_location
```

The input file must be a .txt or .tck file in valid [TChecker syntax](https://github.com/ticktac-project/tchecker/wiki/TChecker-file-format).  
For a given network of timed automata, every possible mutation is generated with the specified operator and written as a .tck file in the specified output directory.  
Mutations that are bisimilar to the original network are written to a seperate directory `bisimilar_mutations` inside the output directory.  
Whether a mutation is bisimilar or not is logged in `bisimilarity_log.csv` in `bisimilar_mutations`.

Note: Output mutation files do not preserve comments of the original TChecker file.

## Literature

1. [B. K. Aichernig, F. Lorber and D. Ničković. Time for Mutants - Model-Based Mutation Testing with Timed Automata (2013)](http://www.ist.tugraz.at/aichernig/publications/papers/tap13-time.pdf)
2. [D. Basile, M. H. ter Beek, S. Lazreg, M. Cordy, A. Legay. Static detection of equivalent mutants in real-time model-based mutation testing (2022)](https://link.springer.com/article/10.1007/s10664-022-10149-y)
3. [D. Cortés, J. Ortiz, D. Basile, J. Aranda, G. Perrouin, P. Schobbens. Time for Networks: Mutation Testing for Timed Automata Networks (2024)](https://ieeexplore.ieee.org/document/10555774)