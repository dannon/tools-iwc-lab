"""Run the plot commands written by `samplot vcf --manual_run` without a shell.

samplot vcf builds each `samplot plot` call as an unquoted shell string from
VCF sample names, chromosome names and SV types, then runs the script through
a shell and ignores failures. Splitting each line ourselves and running it as
an argument vector keeps metacharacters in that metadata inert, and lets a
failed plot fail the job instead of silently dropping an image.

Splitting on whitespace still lets a value with a space in it turn into extra
arguments, so each command may only use the options samplot vcf 1.3.0 itself
writes, once each, and must write its single image directly into the output
directory.
"""

import os
import shlex
import subprocess
import sys

# the options in samplot vcf's command template; -c/-s/-e repeat for breakends
ONCE = {"-z", "-n", "-t", "-o", "-d", "-b", "--start_ci", "--end_ci"}
REPEATABLE = {"-c", "-s", "-e"}
# passed through by the wrapper, always straight after "samplot plot"
LEADING = ["--reference", "reference.fa"]


def check(argv, out_root):
    if argv[:2] != ["samplot", "plot"]:
        return "not a samplot plot command"
    args = argv[2:]
    if args[:2] == LEADING:
        args = args[2:]
    options = [a for a in args if a.startswith("-")]
    for option in options:
        if option not in ONCE and option not in REPEATABLE:
            return "unexpected option %s" % option
        if option in ONCE and options.count(option) > 1:
            return "option %s given more than once" % option
    if "-o" not in args[:-1]:
        return "no output file"
    target = os.path.realpath(args[args.index("-o") + 1])
    if os.path.dirname(target) != out_root:
        return "output file outside the output directory"
    return None


def main(command_file, out_dir):
    out_root = os.path.realpath(out_dir)
    failed = 0
    with open(command_file) as fh:
        lines = [line.strip() for line in fh if line.strip()]
    for line in lines:
        try:
            argv = shlex.split(line)
        except ValueError as e:
            sys.exit("Cannot parse a samplot command (%s): %s" % (e, line))
        problem = check(argv, out_root)
        if problem:
            sys.exit("Refusing to run a samplot plot command (%s): %s" % (problem, line))
        if subprocess.run(argv).returncode != 0:
            print("samplot plot failed: %s" % line, file=sys.stderr)
            failed += 1
    if failed:
        sys.exit("%d of %d samplot plot commands failed" % (failed, len(lines)))


if __name__ == "__main__":
    main(sys.argv[1], sys.argv[2])
