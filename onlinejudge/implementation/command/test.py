# Python Version: 3.x
import math
import sys
import time

import onlinejudge.implementation.command.utils as cutils
import onlinejudge.implementation.logging as log
import onlinejudge.implementation.utils as utils


def compare_as_floats(xs, ys, error):
    def f(x):
        try:
            y = float(x)
            if not math.isfinite(y):
                log.warning("not an real number found: %f", y)
            return y
        except ValueError:
            return x

    xs = list(map(f, xs.split()))
    ys = list(map(f, ys.split()))
    if len(xs) != len(ys):
        return False
    for x, y in zip(xs, ys):
        if isinstance(x, float) and isinstance(y, float):
            if not math.isclose(x, y, rel_tol=error, abs_tol=error):
                return False
        else:
            if x != y:
                return False
    return True


def test(args):
    # prepare
    if not args.test:
        args.test = cutils.glob_with_format(args.directory, args.format)  # by default
    if args.ignore_backup:
        args.test = cutils.drop_backup_or_hidden_files(args.test)
    tests = cutils.construct_relationship_of_files(
        args.test, args.directory, args.format
    )
    if args.error:  # float mode
        match = lambda a, b: compare_as_floats(a, b, args.error)
    else:

        def match(a, b):
            if a == b:
                return True
            if args.rstrip and a.rstrip(rstrip_targets) == b.rstrip(rstrip_targets):
                log.warning("WA if no rstrip")
                return True
            return False

    rstrip_targets = " \t\r\n\f\v\0"  # ruby's one, follow AnarchyGolf
    slowest, slowest_name = -1, ""
    ac_count = 0

    for name, it in sorted(tests.items()):
        is_printed_input = not args.print_input

        def print_input():
            nonlocal is_printed_input
            if not is_printed_input:
                is_printed_input = True
                with open(it["in"]) as inf:
                    log.emit("input:\n%s", log.bold(inf.read()))

        log.emit("")
        log.info("%s", name)

        # run the binary
        with open(it["in"]) as inf:
            begin = time.perf_counter()
            answer, proc = utils.exec_command(
                args.command, shell=True, stdin=inf, timeout=args.tle
            )
            end = time.perf_counter()
            answer = answer.decode()
            if slowest < end - begin:
                slowest = end - begin
                slowest_name = name
            log.status("time: %f sec", end - begin)
            proc.terminate()

        # check TLE, RE or not
        result = "AC"
        if proc.returncode is None:
            log.failure(log.red("TLE"))
            result = "TLE"
            print_input()
        elif proc.returncode != 0:
            log.failure(log.red("RE") + ": return code %d", proc.returncode)
            result = "RE"
            print_input()

        # check WA or not
        if "out" in it:
            with open(it["out"]) as outf:
                correct = outf.read()
            # compare
            if args.mode == "all":
                if not match(answer, correct):
                    log.failure(log.red("WA"))
                    print_input()
                    if not args.silent:
                        log.emit("output:\n%s", log.bold(answer))
                        log.emit("expected:\n%s", log.bold(correct))
                    result = "WA"
            elif args.mode == "line":
                answer = answer.splitlines()
                correct = correct.splitlines()
                for i, (x, y) in enumerate(
                    zip(answer + [None] * len(correct), correct + [None] * len(answer))
                ):
                    if x is None and y is None:
                        break
                    elif x is None:
                        print_input()
                        log.failure(
                            log.red("WA") + ': line %d: line is nothing: expected "%s"',
                            i + 1,
                            log.bold(y),
                        )
                        result = "WA"
                    elif y is None:
                        print_input()
                        log.failure(
                            log.red("WA") + ': line %d: unexpected line: output "%s"',
                            i + 1,
                            log.bold(x),
                        )
                        result = "WA"
                    elif not match(x, y):
                        print_input()
                        log.failure(
                            log.red("WA") + ': line %d: output "%s": expected "%s"',
                            i + 1,
                            log.bold(x),
                            log.bold(y),
                        )
                        result = "WA"
            else:
                assert False
        else:
            if not args.silent:
                log.emit(log.bold(answer))
        if result == "AC":
            log.success(log.green("AC"))
            ac_count += 1

    # summarize
    log.emit("")
    log.status("slowest: %f sec  (for %s)", slowest, slowest_name)
    if ac_count == len(tests):
        log.success("test " + log.green("success") + ": %d cases", len(tests))
    else:
        log.failure(
            "test " + log.red("failed") + ": %d AC / %d cases", ac_count, len(tests)
        )
        sys.exit(1)
