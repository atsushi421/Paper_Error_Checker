import argparse
import glob
import os
import re
from logging import getLogger
from typing import Dict, List, Tuple

import yaml

logger = getLogger(__name__)


def option_parser():
    arg_parser = argparse.ArgumentParser()
    arg_parser.add_argument(
        "-d",
        "--check_dir",
        required=True,
        type=str,
        help="Path to directory containing tex files to be checked"
    )
    args = arg_parser.parse_args()

    return args.check_dir


class Checker():
    def __init__(
        self,
        file_paths: List[str]
    ) -> None:
        # Create target path dict
        self._target_paths = {"all": file_paths}
        self._target_paths["introduction"] = [p for p in file_paths
                                              if "intro" in p.lower()]
        self._target_paths["abstract"] = [p for p in file_paths
                                          if "abst" in p.lower()]
        self._target_paths["except for abstract"] = [p for p in file_paths
                                                     if "abst" not in p.lower()]

    def check(
        self,
        options: Dict
    ) -> List[str]:
        check_type, args_dict = self._option_perse(options)
        if(check_type == "line"):
            return self._check_per_line(**args_dict)
        else:
            raise NotImplementedError()

    def _option_perse(
        self,
        options: Dict
    ) -> Tuple[str, Dict]:
        args = {"pattern": options["pattern"]}
        flags_str = options.get("flags")
        if(flags_str == "ignorecase"):
            args["flags"] = re.IGNORECASE
        else:
            args["flags"] = None

        args["target"] = options.get("target", "all")
        check_type = options.get("check type", "line")

        return check_type, args

    def _check_per_line(
        self,
        pattern: str,
        flags,
        target: str
    ) -> List[str]:
        errors = []
        for tex_path in self._target_paths[target]:
            with open(tex_path, "r", encoding="utf-8") as f:
                lines = f.readlines()
            for line_count, line in enumerate(lines):
                if(flags):
                    matches = re.finditer(pattern, line, flags)
                else:
                    matches = re.finditer(pattern, line)
                if(matches):
                    for match in matches:
                        head = line[:match.start()]
                        tail = line[match.end():]
                        match_str = line[match.start():match.end()]
                        out = head + "\033[91m" + match_str + "\033[0m" + tail

                        errors.append(" | ".join([
                            os.path.basename(tex_path),
                            str(line_count+1),
                            out])
                        )

        return errors


def print_log(
    msg: str,
    level: str,
    errors: List[str]
) -> None:
    if(errors):
        if(level == "info"):
            logger.info(msg)
        elif(level == "warning"):
            logger.warning(msg)
        elif(level == "error"):
            logger.error(msg)
        else:
            raise NotImplementedError

        for error in errors:
            print(f"\t{error}")
        print("------------------------------------------------------------")


def main(check_dir):
    tex_paths = glob.glob(f"{check_dir}/**/*.tex",
                          recursive=True)
    checker = Checker(tex_paths)

    # Load check list
    with open(
        f"{os.path.dirname(__file__)}/check_lists/check_list.yaml",
        "r"
    ) as f:
        check_list = yaml.safe_load(f)

    # Check
    for msg, options in check_list.items():
        errors = checker.check(options)
        print_log(msg, options["level"], errors)


if __name__ == "__main__":
    check_dir = option_parser()
    main(check_dir)
