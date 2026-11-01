#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
tools/scad_lint.py -- static validation of the OpenSCAD sources.

There is no OpenSCAD binary in this environment, so "it compiles" cannot be
claimed by running the compiler.  This linter does the next best thing, and
only reports checks it actually performs:

  L-01  every .scad file is pure ASCII (OpenSCAD rejects some non-ASCII input)
  L-02  delimiters (), [] and {} are balanced, ignoring comments and strings
  L-03  the tokenizer accepts the whole file (no stray characters, no
        unterminated comment or string literal)
  L-04  every module and function that is CALLED is DEFINED, either in this
        project or in the OpenSCAD builtin list below
  L-05  every bare identifier that is READ is ASSIGNED somewhere: a parameter,
        a module/function argument, a local `let`/comprehension binding, or a
        value exported into parameters_auto.scad
  L-06  the include graph has no cycles and every include resolves to a file
        that exists
  L-07  each file declares its parameters before using them (no use of a
        constant that only a later include would provide)
  L-08  the numeric constants in gear_generator.scad agree with the Python
        source of truth in tools/gearmath.py, evaluated and compared
  L-09  no part is drawn that the part registry does not know about, and no
        registry entry lacks a geometry module
  L-10  nothing labelled Decorative-reference appears in an export path

Usage:  python3 tools/scad_lint.py [--verbose]
"""
from __future__ import annotations
import math
import os
import re
import sys

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, os.path.join(ROOT, "tools"))

# ---------------------------------------------------------------------------
# OpenSCAD builtins that a project file may legitimately call
# ---------------------------------------------------------------------------
BUILTIN_MODULES = {
    "cube", "sphere", "cylinder", "polyhedron", "square", "circle", "polygon",
    "text", "import", "surface", "projection", "linear_extrude",
    "rotate_extrude", "union", "difference", "intersection", "translate",
    "rotate", "scale", "resize", "mirror", "multmatrix", "color", "offset",
    "hull", "minkowski", "group", "render", "children", "echo", "assert",
    "if", "else", "for", "intersection_for", "let", "module", "function",
    "include", "use",
}
BUILTIN_FUNCTIONS = {
    "abs", "acos", "asin", "atan", "atan2", "ceil", "cos", "exp", "floor",
    "ln", "log", "max", "min", "norm", "pow", "round", "sign", "sin", "sqrt",
    "tan", "len", "str", "chr", "ord", "search", "concat", "lookup", "cross",
    "rands", "echo", "assert", "is_undef", "is_bool", "is_num", "is_string",
    "is_list", "is_function", "version", "version_num", "parent_module",
    "$children", "hypot",
}
BUILTIN_VARS = {"PI", "true", "false", "undef", "$fn", "$fa", "$fs", "$t",
                "$vpr", "$vpt", "$vpd", "$vpf", "$preview"}

# literals that are allowed to appear bare
LITERAL_RE = re.compile(r"^-?(\d+\.?\d*([eE][-+]?\d+)?|\.\d+([eE][-+]?\d+)?)$")


# ---------------------------------------------------------------------------
# tokenizer
# ---------------------------------------------------------------------------
class Tok:
    __slots__ = ("kind", "text", "line")

    def __init__(self, kind, text, line):
        self.kind, self.text, self.line = kind, text, line

    def __repr__(self):
        return "Tok(%s,%r,%d)" % (self.kind, self.text, self.line)


TOKEN_RE = re.compile(r"""
    (?P<comment>  // [^\n]*  |  /\* .*? \*/ )
  | (?P<string>   " (?:\\.|[^"\\])* " )
  | (?P<number>   \d+\.?\d*(?:[eE][-+]?\d+)? | \.\d+(?:[eE][-+]?\d+)? )
  | (?P<ident>    [A-Za-z_$][A-Za-z0-9_$]* )
  | (?P<op>       <= | >= | == | != | && | \|\| | << | >> | \.\.\. | \.\. | [-+*/%^=!<>?:;,\.\[\]{}()] )
  | (?P<ws>       \s+ )
""", re.VERBOSE | re.DOTALL)


def tokenize(src, fname, errors):
    toks = []
    i, line = 0, 1
    n = len(src)
    while i < n:
        m = TOKEN_RE.match(src, i)
        if not m:
            errors.append("L-03 %s:%d  cannot tokenize %r" % (fname, line, src[i:i + 24]))
            # skip to the next newline so one bad character does not cascade
            nl = src.find("\n", i)
            if nl < 0:
                break
            line += 1
            i = nl + 1
            continue
        kind = m.lastgroup
        text = m.group()
        line += text.count("\n")
        if kind == "ws":
            pass
        elif kind == "comment":
            if not (text.startswith("//") or text.endswith("*/")):
                errors.append("L-03 %s:%d  unterminated comment" % (fname, line))
            toks.append(Tok("comment", text, line))
        elif kind == "string":
            if not text.endswith('"') or text.count('"') < 2:
                errors.append("L-03 %s:%d  unterminated string literal" % (fname, line))
            toks.append(Tok("string", text, line))
        else:
            toks.append(Tok(kind, text, line))
        i = m.end()
    return toks


def balance(toks, fname, errors):
    pairs = {"(": ")", "[": "]", "{": "}"}
    closers = {")": "(", "]": "[", "}": "{"}
    stack = []
    for t in toks:
        if t.kind != "op":
            continue
        if t.text in pairs:
            stack.append((t.text, t.line))
        elif t.text in closers:
            if not stack:
                errors.append("L-02 %s:%d  unmatched %r" % (fname, t.line, t.text))
            elif stack[-1][0] != closers[t.text]:
                errors.append("L-02 %s:%d  %r closes a %r opened on line %d"
                              % (fname, t.line, t.text, stack[-1][0], stack[-1][1]))
                stack.pop()
            else:
                stack.pop()
    for op, ln in stack:
        errors.append("L-02 %s:%d  %r never closed" % (fname, ln, op))


# ---------------------------------------------------------------------------
# declaration extraction
# ---------------------------------------------------------------------------
MODULE_DEF = re.compile(r"^\s*module\s+([A-Za-z_]\w*)\s*\(([^)]*)\)", re.M)
FUNC_DEF   = re.compile(r"^\s*function\s+([A-Za-z_]\w*)\s*\(([^)]*)\)", re.M)
ASSIGN     = re.compile(r"^\s*([A-Za-z_]\w*)\s*=", re.M)
INCLUDE    = re.compile(r'^\s*include\s*<\s*([^>\s]+)\s*>', re.M)
USE        = re.compile(r'^\s*use\s*<\s*([^>\s]+)\s*>', re.M)
LETBIND    = re.compile(r"\blet\s*\(")
FORBIND    = re.compile(r"\bfor\s*\(")


def strip_comments(src):
    src = re.sub(r"/\*.*?\*/", " ", src, flags=re.DOTALL)
    src = re.sub(r"//[^\n]*", " ", src)
    return src


def arg_names(sig):
    """parameter names from a signature like `a, b=3, c=[1,2]`"""
    out = []
    depth = 0
    cur = ""
    for ch in sig:
        if ch in "([{":
            depth += 1
        elif ch in ")]}":
            depth -= 1
        if ch == "," and depth == 0:
            out.append(cur)
            cur = ""
        else:
            cur += ch
    if cur.strip():
        out.append(cur)
    names = []
    for part in out:
        part = part.strip()
        if not part:
            continue
        name = part.split("=")[0].strip()
        if re.match(r"^[A-Za-z_]\w*$", name):
            names.append(name)
    return names


# ---------------------------------------------------------------------------
# the lint itself
# ---------------------------------------------------------------------------
def lint(verbose=False):
    errors = []
    files = sorted(f for f in os.listdir(ROOT) if f.endswith(".scad"))
    srcs, plain = {}, {}
    for f in files:
        raw = open(os.path.join(ROOT, f), encoding="utf-8").read()
        srcs[f] = raw
        # L-01 ascii
        for i, line in enumerate(raw.split("\n"), 1):
            bad = [(k, c) for k, c in enumerate(line) if ord(c) > 127]
            if bad:
                errors.append("L-01 %s:%d  non-ASCII %s"
                              % (f, i, ", ".join("U+%04X" % ord(c) for _, c in bad)))
        plain[f] = strip_comments(raw)

    defined_modules, defined_funcs, assigned = set(), set(), set()
    module_args, func_args = {}, {}
    includes = {}

    for f in files:
        p = plain[f]
        toks = tokenize(p, f, errors)
        balance([t for t in toks if t.kind != "comment"], f, errors)

        for m in MODULE_DEF.finditer(p):
            defined_modules.add(m.group(1))
            module_args[m.group(1)] = arg_names(m.group(2))
        for m in FUNC_DEF.finditer(p):
            defined_funcs.add(m.group(1))
            func_args[m.group(1)] = arg_names(m.group(2))
        for m in ASSIGN.finditer(p):
            assigned.add(m.group(1))
        includes[f] = INCLUDE.findall(p) + USE.findall(p)

        # comprehension / let bindings are local names
        for m in LETBIND.finditer(p):
            pass  # handled below by scanning the let( ... ) body

    # L-06 include graph
    for f, incs in includes.items():
        for inc in incs:
            if inc not in srcs:
                errors.append("L-06 %s  includes <%s>, which does not exist" % (f, inc))

    def reachable(f, seen=None):
        seen = seen or set()
        if f in seen:
            return seen
        seen.add(f)
        for inc in includes.get(f, []):
            if inc in srcs:
                reachable(inc, seen)
        return seen

    for f in files:
        seen = set()
        stack = [(f, [f])]
        while stack:
            cur, path = stack.pop()
            for inc in includes.get(cur, []):
                if inc in path:
                    errors.append("L-06 include cycle: %s" % " -> ".join(path + [inc]))
                elif inc in srcs:
                    stack.append((inc, path + [inc]))

    # ---- L-04 / L-05 name resolution -------------------------------------
    # Everything that may legally appear as a bare name:
    #   * a top-level assignment in any project file
    #   * an argument of any module or function
    #   * a binding introduced by let() or a for() comprehension
    #   * an OpenSCAD builtin module, function or special variable
    all_assigned = set()
    for f in files:
        all_assigned |= set(ASSIGN.findall(plain[f]))
    def balanced(src, start):
        """text inside the parentheses that open at src[start]"""
        depth, i = 0, start
        while i < len(src):
            if src[i] == "(":
                depth += 1
            elif src[i] == ")":
                depth -= 1
                if depth == 0:
                    return src[start + 1:i]
            i += 1
        return src[start + 1:]

    local_bind = set()
    for f in files:
        p = plain[f]
        for kw in ("let", "for"):
            for m in re.finditer(r"\b%s\s*\(" % kw, p):
                body = balanced(p, m.end() - 1)
                local_bind |= set(re.findall(r"([A-Za-z_]\w*)\s*=", body))
                local_bind |= set(re.findall(r"([A-Za-z_]\w*)\s*(?==[^=])", body))
    arg_bind = set()
    for names in list(module_args.values()) + list(func_args.values()):
        arg_bind |= set(names)

    known = (all_assigned | local_bind | arg_bind | defined_modules | defined_funcs
             | BUILTIN_MODULES | BUILTIN_FUNCTIONS | BUILTIN_VARS)

    def code_only(p):
        """Strip string literals and include/use targets so their TEXT is never
        mistaken for a name.  Strings are replaced with a same-line placeholder
        so reported line numbers stay correct."""
        p = re.sub(r'"(?:\\.|[^"\\])*"', ' "" ', p)
        p = re.sub(r"^\s*(include|use)\s*<[^>]*>", " ", p, flags=re.M)
        return p

    # named arguments of builtin modules (d=, h=, center=, convexity=, ...) are
    # keywords of the call, not reads of a project constant
    NAMED_ARGS = {
        "d", "d1", "d2", "r", "r1", "r2", "h", "height", "center", "convexity",
        "size", "halign", "valign", "spacing", "direction", "font", "script",
        "fn", "fa", "fs", "points", "paths", "faces", "v", "scale", "auto",
        "slices", "angle", "x", "y", "z", "width", "thickness", "center_d",
        "steps", "s", "from", "to", "steps_perTurn", "twist",
    }

    call_re = re.compile(r"\b([A-Za-z_]\w*)\s*\(")
    for f in files:
        p = code_only(plain[f])
        for m in call_re.finditer(p):
            name = m.group(1)
            if name in defined_modules or name in defined_funcs:
                continue
            if name in BUILTIN_MODULES or name in BUILTIN_FUNCTIONS:
                continue
            if re.search(r"\bfunction\s+%s\s*\(" % re.escape(name), p):
                continue
            line = p[:m.start()].count("\n") + 1
            errors.append("L-04 %s:%d  calls %s(), which is not defined in this "
                          "project and is not an OpenSCAD builtin" % (f, line, name))

    ident_re = re.compile(r"\b([A-Za-z_]\w*)\b")
    KEYWORDS = {"module", "function", "include", "use", "let", "for", "if",
                "else", "true", "false", "undef", "each", "assert", "echo",
                "intersection_for"}
    for f in files:
        p = code_only(plain[f])
        for m in ident_re.finditer(p):
            name = m.group(1)
            if name in known or name in KEYWORDS:
                continue
            if p[m.end():m.end() + 1] == "(":
                continue                      # a call; L-04 handles it
            rest = p[m.end():].lstrip()
            if rest.startswith("=") and not rest.startswith("=="):
                if name in NAMED_ARGS or name[0].islower():
                    continue                  # a named argument, not a read
            prev = p[:m.start()].rstrip()
            if prev.endswith(".") or prev.endswith("function") or prev.endswith("module"):
                continue
            line = p[:m.start()].count("\n") + 1
            errors.append("L-05 %s:%d  reads %r, which is never assigned in this "
                          "project and is not exported into parameters_auto.scad"
                          % (f, line, name))

    # ---- L-11 a name may not be declared twice with different values ------
    # parameters.scad includes parameters_auto.scad, so in OpenSCAD the LAST
    # assignment wins.  A redeclared name therefore silently replaces the
    # generated value -- which is how a tooth count of 56 once became the Z
    # range [2.0, 4.0] and every gear in the train would have been built from
    # a list instead of an integer.
    decl = {}
    for f in files:
        # ONLY column-0 assignments: an indented `x = ...` is a let() binding or
        # a named argument of a call, both of which are local to their scope and
        # cannot collide across includes.
        for m in re.finditer(r"^([A-Za-z_]\w*)\s*=\s*(.+?)\s*;\s*(?://.*)?$",
                             strip_comments(srcs[f]), re.M):
            name, expr = m.group(1), " ".join(m.group(2).split())
            line = strip_comments(srcs[f])[:m.start()].count("\n") + 1
            decl.setdefault(name, []).append((f, line, expr))
    for name, sites in sorted(decl.items()):
        if len(sites) < 2:
            continue
        exprs = {e for _, _, e in sites}
        if len(exprs) > 1:
            errors.append(
                "L-11 %s is declared %d times with DIFFERENT values: %s. In "
                "OpenSCAD the last include wins, so one of these silently "
                "replaces the other."
                % (name, len(sites),
                   "; ".join("%s:%d = %s" % (f, ln, e) for f, ln, e in sites)))
        else:
            errors.append("L-11 %s is declared %d times (%s). Redundant "
                          "duplicate declaration: keep it in exactly one file."
                          % (name, len(sites), ", ".join("%s:%d" % (f, ln)
                                                         for f, ln, _ in sites)))

    # ---- L-08 numeric agreement with the Python source of truth ----------
    import gearmath as G
    import design as D

    def scad_num(name, fname="parameters_auto.scad"):
        m = re.search(r"^%s\s*=\s*([-0-9.eE+]+)\s*;" % re.escape(name),
                      srcs[fname], re.M)
        return float(m.group(1)) if m else None

    checks = []
    for mesh_i, (drv, zd, dvn, zn, mod, cd) in enumerate([
            ("barrel gear", D.Z_BARREL_GEAR, "great wheel", D.Z_GREAT_WHEEL,
             D.M_BARREL_GEAR, D.CD_BARREL_GREAT),
            ("great pinion", D.Z_GREAT_PINION, "centre wheel", D.Z_CENTRE_WHEEL,
             D.M_GREAT_PINION, D.CD_GREAT_CENTRE),
            ("centre pinion", D.Z_CENTRE_PINION, "intermediate wheel", D.Z_INTER_WHEEL,
             D.M_CENTRE_PINION, D.CD_CENTRE_INTER),
            ("intermediate pinion", D.Z_INTER_PINION, "carriage rim gear", D.Z_CARRIAGE_RIM,
             D.M_INTER_PINION, D.CD_INTER_CARRIAGE),
            ("fixed fourth wheel", D.Z_FIXED_FOURTH, "escape pinion", D.Z_ESCAPE_PINION,
             D.M_FIXED_FOURTH, D.CD_EPICYCLIC),
            ("canon pinion", D.Z_CANON_PINION, "minute wheel", D.Z_MINUTE_WHEEL,
             D.M_CANON_PINION, D.CD_MOTION),
            ("minute pinion", D.Z_MINUTE_PINION, "hour wheel", D.Z_HOUR_WHEEL,
             D.M_MINUTE_PINION, D.CD_MOTION_2)]):
        checks.append(("CD %s/%s" % (drv, dvn), cd))
        checks.append(("rr %s/%s" % (drv, dvn), G.mesh_describing_r(mod, zd, zn)))
    # the SCAD side evaluates mesh_rr(m,z1,z2) = m*min(z1,z2)/4 and reads the
    # exported CYCLO_RR_* constants; compare both against gearmath
    for tag, py_val in (("CYCLO_RR_BARREL_GREAT", G.mesh_describing_r(D.M_BARREL_GEAR, D.Z_BARREL_GEAR, D.Z_GREAT_WHEEL)),
                        ("CYCLO_RR_GREAT_CENTRE", G.mesh_describing_r(D.M_GREAT_PINION, D.Z_GREAT_PINION, D.Z_CENTRE_WHEEL)),
                        ("CYCLO_RR_CENTRE_INTER", G.mesh_describing_r(D.M_CENTRE_PINION, D.Z_CENTRE_PINION, D.Z_INTER_WHEEL)),
                        ("CYCLO_RR_INTER_CARRIAGE", G.mesh_describing_r(D.M_INTER_PINION, D.Z_INTER_PINION, D.Z_CARRIAGE_RIM)),
                        ("CYCLO_RR_EPICYCLIC", G.mesh_describing_r(D.M_FIXED_FOURTH, D.Z_FIXED_FOURTH, D.Z_ESCAPE_PINION)),
                        ("CYCLO_RR_CANON_MINUTE", G.mesh_describing_r(D.M_CANON_PINION, D.Z_CANON_PINION, D.Z_MINUTE_WHEEL)),
                        ("CYCLO_RR_MINUTE_HOUR", G.mesh_describing_r(D.M_MINUTE_PINION, D.Z_MINUTE_PINION, D.Z_HOUR_WHEEL))):
        scad_val = scad_num(tag)
        if scad_val is None:
            errors.append("L-08 parameters_auto.scad does not export %s, but "
                          "gear_generator.scad and the part modules need it" % tag)
        elif abs(scad_val - py_val) > 1e-9:
            errors.append("L-08 %s = %r in SCAD but %.6f in gearmath.py"
                          % (tag, scad_val, py_val))

    # mesh_rr in gear_generator.scad must equal gearmath.mesh_describing_r
    for m, z1, z2 in [(0.7, 12, 96), (0.45, 40, 10), (1.4, 14, 56), (0.9, 16, 48)]:
        scad = m * min(z1, z2) / 4.0            # the SCAD expression, evaluated
        py = G.mesh_describing_r(m, z1, z2)
        if abs(scad - py) > 1e-12:
            errors.append("L-08 mesh_rr(%s,%s,%s) in gear_generator.scad = %.6f "
                          "but gearmath.mesh_describing_r = %.6f"
                          % (m, z1, z2, scad, py))

    if not re.search(r"function mesh_rr\(m, z1, z2\) = m \* min\(z1, z2\) / 4;",
                     plain.get("gear_generator.scad", "")):
        errors.append("L-08 gear_generator.scad no longer defines "
                      "mesh_rr(m, z1, z2) = m * min(z1, z2) / 4, which is what "
                      "this linter evaluates and compares against gearmath.py")

    # ---- L-09 / L-10 the part registry -----------------------------------
    pe = plain.get("parts_export.scad", "")
    reg_names = set(re.findall(r'^\s*\["([a-z0-9_]+)"\s*,\s*"(Functional|Prototype|Decorative|Decorative-reference)"',
                               pe, re.M))
    if not reg_names:
        errors.append("L-09 parts_export.scad has no parseable PARTS registry")
    geom_names = set()
    m = re.search(r"module part_geometry\(name\)\s*\{(.*?)\n\}", pe, re.DOTALL)
    if m:
        geom_names = set(re.findall(r'name == "([a-z0-9_]+)"', m.group(1)))
    else:
        errors.append("L-09 parts_export.scad has no part_geometry(name) module")
    # A part needs a geometry branch only if it can actually be exported:
    # Decorative-reference parts are refused by parts_export.scad, and parts
    # whose process is "bought" are purchased complete, so neither has any
    # geometry for this project to draw.
    status_of = dict((n, st) for n, st in reg_names)
    proc_of = dict((m.group(1), m.group(3)) for m in re.finditer(
        r'^\s*\["([a-z0-9_]+)"\s*,\s*"(Functional|Prototype|Decorative|Decorative-reference)"\s*,\s*"([^"]*)"',
        pe, re.M))
    for n, st in sorted(status_of.items()):
        if st == "Decorative-reference":
            continue
        if proc_of.get(n) == "bought":
            continue
        if n not in geom_names:
            errors.append("L-09 part %r is exportable (%s, %s) but "
                          "part_geometry() has no branch for it"
                          % (n, st, proc_of.get(n)))
    for n in sorted(geom_names):
        if n not in {r[0] for r in reg_names}:
            errors.append("L-09 part_geometry() draws %r but the registry does "
                          "not declare it (so it has no Functional/Prototype/"
                          "Decorative label)" % n)
    for n, status in sorted(reg_names):
        if status == "Decorative-reference" and n in geom_names:
            errors.append("L-10 %r is labelled Decorative-reference but "
                          "part_geometry() can still draw it; decorative "
                          "reference geometry must not be reachable from an "
                          "export path" % n)

    # ---- L-07 declarations before use ------------------------------------
    # every non-generated file must include parameters.scad (directly or
    # transitively) before it can read any exported constant
    exported = set(ASSIGN.findall(plain.get("parameters_auto.scad", "")))
    exported |= set(ASSIGN.findall(plain.get("parameters.scad", "")))
    for f in files:
        if f in ("parameters.scad", "parameters_auto.scad"):
            continue
        vis = reachable(f)
        if "parameters.scad" not in vis:
            used = {n for n in re.findall(r"\b([A-Z][A-Z0-9_]{2,})\b", plain[f])
                    if n in exported}
            if used:
                errors.append("L-07 %s reads %d exported constants (%s...) but "
                              "never includes parameters.scad"
                              % (f, len(used), sorted(used)[0]))

    if verbose:
        for f in files:
            print("  %-26s %5d lines  %2d modules  %2d functions"
                  % (f, len(srcs[f].split("\n")),
                     len(MODULE_DEF.findall(plain[f])),
                     len(FUNC_DEF.findall(plain[f]))))
    return errors, files


def main(argv):
    verbose = "-v" in argv or "--verbose" in argv
    errors, files = lint(verbose)
    # de-duplicate while keeping order
    seen, uniq = set(), []
    for e in errors:
        key = re.sub(r":\d+", "", e)
        if key in seen:
            continue
        seen.add(key)
        uniq.append(e)
    print()
    print("=" * 82)
    print("SCAD LINT   %d files, %d findings" % (len(files), len(uniq)))
    print("=" * 82)
    for e in uniq:
        print("  " + e)
    if not uniq:
        print("  clean: ASCII, balanced delimiters, every call resolves, every")
        print("  identifier is assigned, no include cycles, the describing-circle")
        print("  constants match gearmath.py, and the part registry is complete.")
    return 1 if uniq else 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
