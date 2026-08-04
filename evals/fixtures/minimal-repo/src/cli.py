import argparse
import re


def slugify(title, separator):
    words = re.findall(r"[a-z0-9]+", title.lower())
    return separator.join(words)


def build_parser():
    parser = argparse.ArgumentParser(prog="slug")
    parser.add_argument("title")
    parser.add_argument("--separator", default="-")
    return parser


def main():
    args = build_parser().parse_args()
    print(slugify(args.title, args.separator))


if __name__ == "__main__":
    main()
