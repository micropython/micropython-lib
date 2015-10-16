import argparse

parser = argparse.ArgumentParser(description="command line program")
parser.add_argument("a")
parser.add_argument("b")
parser.add_argument("c")
args = parser.parse_args(["1", "2", "3"])
assert args.a == "1" and args.b == "2" and args.c == "3"

parser = argparse.ArgumentParser()
parser.add_argument("-a", action="store_true")
parser.add_argument("-b", default=123)
args = parser.parse_args([])
assert args.a == False and args.b == 123
args = parser.parse_args(["-a"])
assert args.a == True and args.b == 123
args = parser.parse_args(["-b", "456"])
assert args.a == False and args.b == "456"

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
