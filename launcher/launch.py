#!/usr/bin/env python

import subprocess
import os
import itertools
import pprint
import argparse
from launcher.adaptors import Adaptors, ShellAdaptor
import glob
import sys
from importlib.machinery import SourceFileLoader
from importlib import util
from typing import Any, Dict


def launch():
    discover_paths = set([os.path.abspath(".")])

    for discover_path in discover_paths:
        sys.path.append(discover_path)

    parser = argparse.ArgumentParser(
        description=
        'Run a task multiple times, controlled by envrironment variables.')
    parser.add_argument("--adaptor",
                        type=str,
                        default="shell",
                        choices=Adaptors.choices(),
                        help='the adaptor with which to run the task.')
    parser.add_argument(
        "--data-dir",
        type=str,
        help=
        'the directory which holds the dataset.  Can also be set through the DATA_DIR environment variable.',
        required=False)
    parser.add_argument(
        "--output-dir",
        type=str,
        help=
        'the directory in which to output results. Can also be set through the OUTPUT_DIR environment variable.',
        required=False)
    subparsers = parser.add_subparsers(title='tasks',
                                       description='valid tasks',
                                       dest="task")

    tasks: Dict[str, Any] = {}
    for discover_path in discover_paths:
        for task in glob.glob("{}/**/tasks.py".format(discover_path),
                              recursive=True):
            loader = SourceFileLoader("task", task)
            spec = util.spec_from_loader("task", loader)
            task = util.module_from_spec(spec)  # type: ignore
            spec.loader.exec_module(task)  # type: ignore
            for c in task.tasks:  # type: ignore
                c.arguments(subparsers)
                tasks[c.name] = c

    assert len(tasks) > 0, "No tasks found in {}".format(discover_paths)

    for adaptor_name in Adaptors.choices():
        adaptor = Adaptors.get(adaptor_name)
        adaptor.arguments(parser)
    args = vars(parser.parse_args())
    if args["data_dir"] is None and "DATA_DIR" in os.environ:
        args["data_dir"] = os.environ["DATA_DIR"]
    if args["output_dir"] is None and "OUTPUT_DIR" in os.environ:
        args["output_dir"] = os.environ["OUTPUT_DIR"]
    assert args["data_dir"] is not None, "No data directory selected."
    assert args["output_dir"] is not None, "No output directory selected."
    assert args["task"] is not None, "No task selected."
    adaptor = Adaptors.get(args["adaptor"])
    task = tasks[args["task"]]

    adaptor.execute(task, args)


if __name__ == "__main__":
    launch()
