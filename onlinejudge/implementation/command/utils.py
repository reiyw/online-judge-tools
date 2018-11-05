# Python Version: 3.x
import collections
import glob
import os
import os.path
import re
import sys

import onlinejudge.implementation.logging as log
import onlinejudge.implementation.utils as utils


def glob_with_format(directory, format):
    table = {}
    table["s"] = "*"
    table["e"] = "*"
    pattern = os.path.join(directory, utils.parcentformat(format, table))
    paths = glob.glob(pattern)
    for path in paths:
        log.debug("testcase globbed: %s", path)
    return paths


def match_with_format(directory, format, path):
    table = {}
    table["s"] = "(?P<name>.+)"
    table["e"] = "(?P<ext>in|out)"
    pattern = re.compile("^" + utils.parcentformat(format, table) + "$")
    path = os.path.normpath(os.path.relpath(path, directory))
    return pattern.match(path)


def path_from_format(directory, format, name, ext):
    table = {}
    table["s"] = name
    table["e"] = ext
    return os.path.join(directory, utils.parcentformat(format, table))


def is_backup_or_hidden_file(path):
    basename = os.path.basename(path)
    return (
        basename.endswith("~")
        or (basename.startswith("#") and basename.endswith("#"))
        or basename.startswith(".")
    )


def drop_backup_or_hidden_files(paths):
    result = []
    for path in paths:
        if is_backup_or_hidden_file(path):
            log.warning("ignore a backup file: %s", path)
        else:
            result += [path]
    return result


def construct_relationship_of_files(paths, directory, format):
    tests = collections.defaultdict(dict)
    for path in paths:
        m = match_with_format(directory, format, os.path.normpath(path))
        if not m:
            log.error("unrecognizable file found: %s", path)
            sys.exit(1)
        name = m.groupdict()["name"]
        ext = m.groupdict()["ext"]
        assert ext not in tests[name]
        tests[name][ext] = path
    for name in tests:
        if "in" not in tests[name]:
            assert "out" in tests[name]
            log.error("dangling output case: %s", tests[name]["out"])
            sys.exit(1)
    if not tests:
        log.error("no cases found")
        sys.exit(1)
    log.info("%d cases found", len(tests))
    return tests
