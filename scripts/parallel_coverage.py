#!/bin/env python

import argparse
import os
import random
import shutil
import subprocess
import sys
import webbrowser
from pathlib import Path


def python_module_to_dir(module: str) -> str:
    parsed_dir = "/".join(module.split("."))
    return Path(f"./{parsed_dir}").resolve()


def parse_arguments():
    parser = argparse.ArgumentParser(description="Run pytest with coverage and optional seed.")
    parser.add_argument("--seed", type=int, help="Seed for randomness")
    parser.add_argument("pytest_args", nargs="*", help="Arguments to pass to pytest")
    return parser.parse_args()


def help_command():
    print("Usage:")
    print(
        "   `pipenv run cov breathecode.events` where events is the name of module and accept "
        "add submodules using the dot(.) character as delimiter."
    )
    print("")
    print("commands:")
    print("   --help see this help message.")
    exit()


def run():
    args = parse_arguments()

    if args.seed is None:
        seed = random.randint(0, 4294967295)
    else:
        seed = args.seed

    module = "breathecode"

    if args.pytest_args:
        module = args.pytest_args[0]

    if module == "--help" or module == "-h":
        help_command()

    dir = python_module_to_dir(module)

    htmlcov_path = os.path.join(os.getcwd(), "htmlcov")

    if os.path.exists(htmlcov_path):
        shutil.rmtree(htmlcov_path)

    command = (
        f'pytest {dir} --disable-pytest-warnings {" ".join(args.pytest_args[1:])} '
        f"--cov={module} --cov-report html -n auto --nomigrations --durations=1"
    )

    print(command)

    env = os.environ.copy()
    env["ENV"] = "test"
    env["RANDOM_SEED"] = str(seed)

    exit_code = subprocess.run(command, env=env, shell=True).returncode

    print()
    print(f"Seed {seed} used, you can provide it locally to reproduce random errors")

    webbrowser.open("file://" + os.path.realpath(os.path.join(os.getcwd(), "htmlcov", "index.html")))

    # python doesn't return 256
    if exit_code:
        sys.exit(1)
