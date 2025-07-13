# tchecker_mutation

This program generates mutations of a TA.
For a given TA, every possible mutation is generated with the specified operator and printed as a .tck file in the specified output directory.

## Usage:

```
$ python mutate.py --in_ta <input_tchecker_file> --out_dir <output_directory> --op <operator> [--val <int>]
```

For example:
```
$ python mutate.py --in_ta ad94.tck --out_dir out --op remove_location
```

## Operator options:

- `no_op`
- `all`

### Attribute changing:

- `change_event`
- `change_constraint_cmp`
- `change_constraint_clock`
- `decrease_constraint_constant`
- `increase_constraint_constant`
- `invert_committed_location`
- `invert_reset`
- `invert_urgent_location`
- `negate_guard`

### Structure changing:

- `add_location`
- `add_transition`
- `change_transition_source`
- `change_transition_target`
- `remove_location`
- `remove_transition`

### Synchronisation changing:

- `invert_sync_weakness`
- `remove_sync`
- `remove_sync_constraint`

## Some Notes:

Input TA must be .txt or .tck file in valid TChecker syntax.\
Output mutation files do not preserve comments of original TChecker file.

For operator option `no_op`, one semantically identical TA is generated.\
For operator option `all`, all possible mutations for each implemented operator are generated.\
For operator options `decrease_constraint_constant`, `increase_constraint_constant` and `all`, an optional integer value to decrease/increase constants by can be specified. 
Default is 1.
