import argparse
import sys
import time
import traceback
from exceptions import TestException
from sys import stdout

import pandas as pd

from collector import Coordinator
from setup import Config


def main_loop(coordinator, select=[], lang=None, test_fail=False):

    collectors = coordinator.start_collectors(select=select,
                                              lang=lang, fail=test_fail)

    stdout.write("\nstarting {} collectors\n".format(len(collectors)))
    stdout.flush()

    i = 0

    for instance in collectors:
        instance.join()
        if instance.err is not None:
            raise instance.err
        i += 1
        stdout.write("{} collector(s) finished\n".format(i))
        stdout.flush()


if __name__ == "__main__":

    parser = argparse.ArgumentParser()
    parser.add_argument('-n', '--seeds', type=int, help="specify number of seeds", default=10)
    parser.add_argument('-l', '--language', help="specify language code of users to gather")
    parser.add_argument('-t', '--test', help="dev only: test for 2 loops only", action="store_true")
    parser.add_argument(
        '-f', '--fail', help="dev only: test unexpected exception", action="store_true")

    args = parser.parse_args()

    config = Config()

    user_details_list = []
    for detail, sqldatatype in config.config["twitter_user_details"].items():
        if sqldatatype is not None:
            user_details_list.append(detail)

    coordinator = Coordinator(seeds=args.seeds)

    k = 0

    while True:

        if args.test:
            k += 1
            if k == 2:
                args.fail = False
            if k == 3:
                break
            stdout.write("\nTEST RUN {}\n".format(k))
            stdout.flush()

        try:
            main_loop(coordinator, select=user_details_list,
                      lang=args.language, test_fail=args.fail)
        except Exception:
            stdout.write("Encountered unexpected exception:\n")
            traceback.print_exc()
            stdout.write("Retrying in 5 seconds.")
            stdout.flush()
            latest_seeds = list(pd.read_csv('latest_seeds.csv', header=None)[0].values)
            coordinator = Coordinator(seed_list=latest_seeds)
            time.sleep(5)