import argparse

parser = argparse.ArgumentParser(description="command line program")
parser.add_argument("a")
parser.add_argument("b")
parser.add_argument(dest="c")
args = parser.parse_args(["1", "2", "3"])
assert args.a == "1" and args.b == "2" and args.c == "3"

parser = argparse.ArgumentParser()
parser.add_argument("-a", action="store_true")
parser.add_argument("-b", default=123)
args = parser.parse_args([])
assert args.a is False and args.b == 123
args = parser.parse_args(["-a"])
assert args.a is True and args.b == 123
args = parser.parse_args(["-b", "456"])
assert args.a is False and args.b == "456"

parser = argparse.ArgumentParser()
parser.add_argument("-a", "--a-opt", action="store_true")
parser.add_argument("-b", "--b-opt", default=123)
parser.add_argument("--c-opt", default="test")
args = parser.parse_args([])
assert args.a_opt is False and args.b_opt == 123 and args.c_opt == "test"
args = parser.parse_args(["--a-opt"])
assert args.a_opt is True and args.b_opt == 123 and args.c_opt == "test"
args = parser.parse_args(["--b-opt", "456"])
assert args.a_opt is False and args.b_opt == "456" and args.c_opt == "test"
args = parser.parse_args(["--c-opt", "override"])
assert args.a_opt is False and args.b_opt == 123 and args.c_opt == "override"

parser = argparse.ArgumentParser()
parser.add_argument("files", nargs="+")
args = parser.parse_args(["a"])
assert args.files == ["a"]
args = parser.parse_args(["a", "b", "c"])
assert args.files == ["a", "b", "c"]

parser = argparse.ArgumentParser()
parser.add_argument("files1", nargs=2)
parser.add_argument("files2", nargs="*")
args = parser.parse_args(["a", "b"])
assert args.files1 == ["a", "b"] and args.files2 == []
args = parser.parse_args(["a", "b", "c"])
assert args.files1 == ["a", "b"] and args.files2 == ["c"]
