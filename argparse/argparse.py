"""
Minimal and functional version of CPython's argparse module.
"""

import sys
from _collections import namedtuple

class _ArgError(BaseException):
    pass

class _Arg:
    def __init__(self, name, dest, action, nargs, const, default, help):
        self.name = name
        self.dest = dest
        self.action = action
        self.nargs = nargs
        self.const = const
        self.default = default
        self.help = help

    def parse(self, args):
        # parse args for this arg
        if self.action == "store":
            if self.nargs == None:
                if args:
                    return args.pop(0)
                else:
                    raise _ArgError("expecting value for %s" % self.name)
            elif self.nargs == "?":
                if args:
                    return args.pop(0)
                else:
                    return self.default
            else:
                if self.nargs == "*":
                    n = -1
                elif self.nargs == "+":
                    if not args:
                        raise _ArgError("expecting value for %s" % self.name)
                    n = -1
                else:
                    n = int(self.nargs)
                ret = []
                stop_at_opt = True
                while args and n != 0:
                    if stop_at_opt and args[0].startswith("-") and args[0] != "-":
                        if args[0] == "--":
                            stop_at_opt = False
                            args.pop(0)
                        else:
                            break
                    else:
                        ret.append(args.pop(0))
                        n -= 1
                if n > 0:
                    raise _ArgError("expecting value for %s" % self.name)
                return ret
        elif self.action == "store_const":
            return self.const
        else:
            assert False

class ArgumentParser:
    def __init__(self, *, description):
        self.description = description
        self.opt = []
        self.pos = []

    def add_argument(self, name, **kwargs):
        action = kwargs.get("action", "store")
        if action == "store_true":
            action = "store_const"
            const = True
            default = kwargs.get("default", False)
        elif action == "store_false":
            action = "store_const"
            const = False
            default = kwargs.get("default", True)
        else:
            const = kwargs.get("const", None)
            default = kwargs.get("default", None)
        if name.startswith("-"):
            list = self.opt
            if name.startswith("--"):
                dest = kwargs.get("dest", name[2:])
            else:
                dest = kwargs.get("dest", name[1:])
        else:
            list = self.pos
            dest = kwargs.get("dest", name)
        list.append(
            _Arg(name, dest, action, kwargs.get("nargs", None),
                const, default, kwargs.get("help", "")))

    def usage(self, full):
        # print short usage
        print("usage: %s [-h]" % sys.argv[0], end="")
        def render_arg(arg):
            if arg.action == "store":
                if arg.nargs is None:
                    return " %s" % arg.dest
                if isinstance(arg.nargs, int):
                    return " %s(x%d)" % (arg.dest, arg.nargs)
                else:
                    return " %s%s" % (arg.dest, arg.nargs)
            else:
                return ""
        for opt in self.opt:
            print(" [%s%s]" % (opt.name, render_arg(opt)), end="")
        for pos in self.pos:
            print(render_arg(pos), end="")
        print()

        if not full:
            return

        # print full information
        print()
        print(self.description)
        if self.pos:
            print("\npositional args:")
            for pos in self.pos:
                print("  %-16s%s" % (pos.name, pos.help))
        print("\noptional args:")
        print("  -h, --help      show this message and exit")
        for opt in self.opt:
            print("  %-16s%s" % (opt.name + render_arg(opt), opt.help))

    def parse_args(self, args=None):
        if args is None:
            args = sys.argv[1:]
        else:
            args = args[:]
        try:
            return self._parse_args(args)
        except _ArgError as e:
            self.usage(False)
            print("error:", e)
            sys.exit(2)

    def _parse_args(self, args):
        # add optional args with defaults
        arg_dest = []
        arg_vals = []
        for opt in self.opt:
            arg_dest.append(opt.dest)
            arg_vals.append(opt.default)

        # parse all args
        parsed_pos = False
        while args or not parsed_pos:
            if args and args[0].startswith("-") and args[0] != "-" and args[0] != "--":
                # optional arg
                a = args.pop(0)
                if a in ("-h", "--help"):
                    self.usage(True)
                    sys.exit(0)
                found = False
                for i, opt in enumerate(self.opt):
                    if a == opt.name:
                        arg_vals[i] = opt.parse(args)
                        found = True
                        break
                if not found:
                    raise _ArgError("unknown option %s" % a)
            else:
                # positional arg
                if parsed_pos:
                    raise _ArgError("extra args: %s" % " ".join(args))
                for pos in self.pos:
                    arg_dest.append(pos.dest)
                    arg_vals.append(pos.parse(args))
                parsed_pos = True

        # build and return named tuple with arg values
        return namedtuple("args", arg_dest)(*arg_vals)
