# tchecker_mutation

This program generates mutations of a TA.
For a given TA, every possible mutation is generated with the specified operator and printed as a .tck file in the specified output directory.

## Usage:

```
$ python mutate.py --in_ta <input_tchecker_file> --out_dir <output_directory> --op <no_op | all | change_event | change_constraint_cmp | decrease_constraint_constant | increase_constraint_constant | invert_reset | flip_committed_location | flip_urgent_location | negate_guard | add_location | add_transition | change_transition_source | change_transition_target | remove_location | remove_transition | remove_sync> [--val <int>]
```

For example:
```
$ python mutate.py --in_ta ad94.tck --out_dir out --op remove_location
```

## Some Notes:

Input TA must be .txt or .tck file in valid TChecker syntax.\
Output mutation files do not preserve comments of original TChecker file.

For operator option `no_op`, one semantically identical TA is generated.\
For operator option `all`, all possible mutations for each implemented operator are generated.\
For operator options `decrease_constraint_constant`, `increase_constraint_constant` and `all`, an optional integer value to decrease/increase constants by can be specified. 
Default is 1.
