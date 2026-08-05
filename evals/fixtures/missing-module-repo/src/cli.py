import argparse

from normalize import normalize_title


def build_parser():
    parser = argparse.ArgumentParser(prog="slug")
    parser.add_argument("title")
    return parser


def main():
    args = build_parser().parse_args()
    print(normalize_title(args.title))


if __name__ == "__main__":
    main()
