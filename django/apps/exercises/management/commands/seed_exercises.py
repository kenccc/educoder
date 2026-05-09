"""Seed the exercise library — 60 exercises (10 × 3 levels × 2 languages).

Idempotent: re-running upserts by slug.
"""
from __future__ import annotations

from django.core.management.base import BaseCommand
from django.db import transaction

from apps.exercises.models import Exercise, Language, Level, TestCase


# ---------- PYTHON ----------
PY_EASY = [
    {
        "slug": "py-hello-world",
        "title": "Hello, World",
        "prompt": "Print exactly the string `Hello, World!`.",
        "starter": 'print("")\n',
        "ref": 'print("Hello, World!")\n',
        "cases": [{"name": "default", "stdin": "", "expected": "Hello, World!"}],
    },
    {
        "slug": "py-echo",
        "title": "Echo input",
        "prompt": "Read a line from stdin and print it back unchanged.",
        "starter": "line = input()\n",
        "ref": "print(input())\n",
        "cases": [
            {"name": "simple", "stdin": "hello\n", "expected": "hello"},
            {"name": "spaces", "stdin": "a b c\n", "expected": "a b c"},
        ],
    },
    {
        "slug": "py-sum-two",
        "title": "Sum two numbers",
        "prompt": "Read two integers (one per line) and print their sum.",
        "starter": "a = int(input())\nb = int(input())\n",
        "ref": "a = int(input())\nb = int(input())\nprint(a + b)\n",
        "cases": [
            {"name": "small",   "stdin": "2\n3\n",      "expected": "5"},
            {"name": "negative","stdin": "-7\n10\n",    "expected": "3"},
            {"name": "zero",    "stdin": "0\n0\n",      "expected": "0", "hidden": True},
        ],
    },
    {
        "slug": "py-even-odd",
        "title": "Even or odd",
        "prompt": "Read an integer. Print `even` if even, else `odd`.",
        "starter": "n = int(input())\n",
        "ref": 'n = int(input())\nprint("even" if n % 2 == 0 else "odd")\n',
        "cases": [
            {"name": "even", "stdin": "4\n",  "expected": "even"},
            {"name": "odd",  "stdin": "7\n",  "expected": "odd"},
            {"name": "neg-even", "stdin": "-2\n", "expected": "even", "hidden": True},
        ],
    },
    {
        "slug": "py-max-of-three",
        "title": "Max of three",
        "prompt": "Read three integers (each on a line). Print the largest.",
        "starter": "a = int(input())\nb = int(input())\nc = int(input())\n",
        "ref": "a, b, c = int(input()), int(input()), int(input())\nprint(max(a,b,c))\n",
        "cases": [
            {"name": "simple", "stdin": "1\n2\n3\n", "expected": "3"},
            {"name": "first",  "stdin": "9\n2\n1\n", "expected": "9"},
            {"name": "neg",    "stdin": "-1\n-9\n-3\n", "expected": "-1", "hidden": True},
        ],
    },
    {
        "slug": "py-reverse-string",
        "title": "Reverse a string",
        "prompt": "Read a line. Print its reverse.",
        "starter": "s = input()\n",
        "ref": "print(input()[::-1])\n",
        "cases": [
            {"name": "word",  "stdin": "hello\n",  "expected": "olleh"},
            {"name": "empty", "stdin": "\n",       "expected": ""},
        ],
    },
    {
        "slug": "py-vowel-count",
        "title": "Count vowels",
        "prompt": "Read a line, print the number of vowels (`aeiou`, case-insensitive).",
        "starter": "s = input()\n",
        "ref": 's = input().lower()\nprint(sum(1 for c in s if c in "aeiou"))\n',
        "cases": [
            {"name": "hello",   "stdin": "hello\n",     "expected": "2"},
            {"name": "AEIOU",   "stdin": "AEIOU\n",     "expected": "5"},
            {"name": "consonants", "stdin": "rhythm\n", "expected": "0", "hidden": True},
        ],
    },
    {
        "slug": "py-square",
        "title": "Square a number",
        "prompt": "Read an integer. Print its square.",
        "starter": "n = int(input())\n",
        "ref": "n = int(input()); print(n*n)\n",
        "cases": [
            {"name": "five",  "stdin": "5\n",  "expected": "25"},
            {"name": "zero",  "stdin": "0\n",  "expected": "0"},
            {"name": "neg",   "stdin": "-3\n", "expected": "9", "hidden": True},
        ],
    },
    {
        "slug": "py-factorial",
        "title": "Factorial",
        "prompt": "Read a non-negative integer N (N ≤ 12). Print N!.",
        "starter": "n = int(input())\n",
        "ref": "import math\nprint(math.factorial(int(input())))\n",
        "cases": [
            {"name": "five", "stdin": "5\n", "expected": "120"},
            {"name": "zero", "stdin": "0\n", "expected": "1"},
            {"name": "ten",  "stdin": "10\n","expected": "3628800", "hidden": True},
        ],
    },
    {
        "slug": "py-fizzbuzz",
        "title": "FizzBuzz",
        "prompt": "Read N. Print FizzBuzz from 1 to N (one per line).",
        "starter": "n = int(input())\n",
        "ref": (
            "n = int(input())\n"
            "for i in range(1, n+1):\n"
            '    if i%15==0: print("FizzBuzz")\n'
            '    elif i%3==0: print("Fizz")\n'
            '    elif i%5==0: print("Buzz")\n'
            "    else: print(i)\n"
        ),
        "cases": [
            {"name": "n=5",  "stdin": "5\n",  "expected": "1\n2\nFizz\n4\nBuzz"},
            {"name": "n=15", "stdin": "15\n", "expected": "1\n2\nFizz\n4\nBuzz\nFizz\n7\n8\nFizz\nBuzz\n11\nFizz\n13\n14\nFizzBuzz", "hidden": True},
        ],
    },
]

PY_MEDIUM = [
    {
        "slug": "py-prime-check",
        "title": "Prime check",
        "prompt": "Read N. Print `yes` if N is prime, else `no`.",
        "starter": "n = int(input())\n",
        "ref": (
            "n = int(input())\n"
            'def isp(x):\n  if x<2: return False\n  for i in range(2,int(x**0.5)+1):\n    if x%i==0: return False\n  return True\n'
            'print("yes" if isp(n) else "no")\n'
        ),
        "cases": [
            {"name": "p7",  "stdin": "7\n",  "expected": "yes"},
            {"name": "p9",  "stdin": "9\n",  "expected": "no"},
            {"name": "p1",  "stdin": "1\n",  "expected": "no", "hidden": True},
            {"name": "p97", "stdin": "97\n", "expected": "yes", "hidden": True},
        ],
    },
    {
        "slug": "py-fibonacci",
        "title": "Nth Fibonacci",
        "prompt": "Read N (0-indexed). Print the Nth Fibonacci number where F(0)=0, F(1)=1.",
        "starter": "n = int(input())\n",
        "ref": (
            "n = int(input())\na,b = 0,1\nfor _ in range(n): a,b = b, a+b\nprint(a)\n"
        ),
        "cases": [
            {"name": "n0",  "stdin": "0\n", "expected": "0"},
            {"name": "n1",  "stdin": "1\n", "expected": "1"},
            {"name": "n10", "stdin": "10\n","expected": "55"},
            {"name": "n20", "stdin": "20\n","expected": "6765", "hidden": True},
        ],
    },
    {
        "slug": "py-palindrome",
        "title": "Palindrome",
        "prompt": "Read a line. Print `yes` if it’s a palindrome (case-insensitive, ignore spaces), else `no`.",
        "starter": "s = input()\n",
        "ref": (
            's = "".join(c.lower() for c in input() if c.isalnum())\n'
            'print("yes" if s == s[::-1] else "no")\n'
        ),
        "cases": [
            {"name": "racecar",     "stdin": "racecar\n", "expected": "yes"},
            {"name": "with-spaces", "stdin": "race car\n","expected": "yes"},
            {"name": "no",          "stdin": "hello\n",   "expected": "no"},
            {"name": "mixed",       "stdin": "Madam\n",   "expected": "yes", "hidden": True},
        ],
    },
    {
        "slug": "py-word-count",
        "title": "Count words",
        "prompt": "Read a line. Print the number of whitespace-separated words.",
        "starter": "line = input()\n",
        "ref": "print(len(input().split()))\n",
        "cases": [
            {"name": "five",   "stdin": "the quick brown fox jumps\n", "expected": "5"},
            {"name": "empty",  "stdin": "\n",                          "expected": "0"},
            {"name": "spaces", "stdin": "  a   b\n",                   "expected": "2", "hidden": True},
        ],
    },
    {
        "slug": "py-sum-list",
        "title": "Sum a list",
        "prompt": "Read N then N integers (one per line). Print their sum.",
        "starter": "n = int(input())\nnumbers = [int(input()) for _ in range(n)]\n",
        "ref": "n = int(input()); print(sum(int(input()) for _ in range(n)))\n",
        "cases": [
            {"name": "three", "stdin": "3\n1\n2\n3\n", "expected": "6"},
            {"name": "neg",   "stdin": "4\n-1\n-2\n3\n4\n", "expected": "4"},
            {"name": "single","stdin": "1\n42\n", "expected": "42", "hidden": True},
        ],
    },
    {
        "slug": "py-anagram",
        "title": "Anagram check",
        "prompt": "Read two lines. Print `yes` if they are anagrams (ignoring case + spaces), else `no`.",
        "starter": "s1 = input()\ns2 = input()\n",
        "ref": (
            "def norm(s): return sorted(c.lower() for c in s if c.isalnum())\n"
            'print("yes" if norm(input()) == norm(input()) else "no")\n'
        ),
        "cases": [
            {"name": "yes",  "stdin": "listen\nsilent\n", "expected": "yes"},
            {"name": "no",   "stdin": "abc\nabd\n",       "expected": "no"},
            {"name": "case", "stdin": "Listen\nSilent\n", "expected": "yes", "hidden": True},
        ],
    },
    {
        "slug": "py-leap-year",
        "title": "Leap year",
        "prompt": "Read a year Y. Print `leap` if it is a leap year, else `not leap`.",
        "starter": "year = int(input())\n",
        "ref": 'y = int(input())\nprint("leap" if (y%4==0 and y%100!=0) or y%400==0 else "not leap")\n',
        "cases": [
            {"name": "2024", "stdin": "2024\n", "expected": "leap"},
            {"name": "1900", "stdin": "1900\n", "expected": "not leap"},
            {"name": "2000", "stdin": "2000\n", "expected": "leap"},
            {"name": "2023", "stdin": "2023\n", "expected": "not leap", "hidden": True},
        ],
    },
    {
        "slug": "py-gcd",
        "title": "Greatest common divisor",
        "prompt": "Read two positive integers. Print their GCD.",
        "starter": "a = int(input())\nb = int(input())\n",
        "ref": "from math import gcd\nprint(gcd(int(input()), int(input())))\n",
        "cases": [
            {"name": "12-8",  "stdin": "12\n8\n",   "expected": "4"},
            {"name": "100-75","stdin": "100\n75\n", "expected": "25"},
            {"name": "coprime","stdin": "13\n7\n",  "expected": "1", "hidden": True},
        ],
    },
    {
        "slug": "py-second-largest",
        "title": "Second largest",
        "prompt": "Read N then N integers. Print the second-largest distinct value (or `none`).",
        "starter": "n = int(input())\nnumbers = [int(input()) for _ in range(n)]\n",
        "ref": (
            "n = int(input()); xs = sorted(set(int(input()) for _ in range(n)), reverse=True)\n"
            'print(xs[1] if len(xs) > 1 else "none")\n'
        ),
        "cases": [
            {"name": "ok",  "stdin": "5\n4\n9\n2\n9\n7\n", "expected": "7"},
            {"name": "all-same", "stdin": "3\n5\n5\n5\n",  "expected": "none"},
            {"name": "two", "stdin": "2\n1\n2\n", "expected": "1", "hidden": True},
        ],
    },
    {
        "slug": "py-string-compress",
        "title": "Run-length encoding",
        "prompt": "Read a string. Print the run-length-encoded form, e.g. `aaabbc` → `a3b2c1`.",
        "starter": "s = input()\n",
        "ref": (
            "import itertools\n"
            "s = input()\n"
            'print("".join(f"{c}{len(list(g))}" for c,g in itertools.groupby(s)) if s else "")\n'
        ),
        "cases": [
            {"name": "easy",   "stdin": "aaabbc\n",   "expected": "a3b2c1"},
            {"name": "single", "stdin": "abc\n",      "expected": "a1b1c1"},
            {"name": "long",   "stdin": "aaaaaa\n",   "expected": "a6", "hidden": True},
        ],
    },
]

PY_HARD = [
    {
        "slug": "py-two-sum",
        "title": "Two sum (indices)",
        "prompt": "Read N, then N integers, then a target T. Print two distinct indices (0-based, smaller first, space-separated) that sum to T. If multiple, print any one. Guaranteed at least one pair.",
        "starter": "n = int(input())\narr = [int(input()) for _ in range(n)]\ntarget = int(input())\n",
        "ref": (
            "n = int(input()); arr = [int(input()) for _ in range(n)]; t = int(input())\n"
            "seen = {}\n"
            "for i,x in enumerate(arr):\n"
            "    if t-x in seen: print(seen[t-x], i); break\n"
            "    seen[x] = i\n"
        ),
        "cases": [
            {"name": "easy",   "stdin": "4\n2\n7\n11\n15\n9\n", "expected": "0 1"},
            {"name": "tail",   "stdin": "3\n3\n2\n4\n6\n",      "expected": "1 2"},
            {"name": "neg",    "stdin": "3\n-1\n-2\n-3\n-5\n",  "expected": "1 2", "hidden": True},
        ],
    },
    {
        "slug": "py-balanced-parens",
        "title": "Balanced parentheses",
        "prompt": "Read a string of `()[]{}`. Print `yes` if balanced, `no` otherwise.",
        "starter": "s = input()\n",
        "ref": (
            "s=input(); pair={')':'(',']':'[','}':'{'}; st=[]\n"
            "ok=True\n"
            "for c in s:\n"
            "    if c in '([{': st.append(c)\n"
            "    elif c in ')]}':\n"
            "        if not st or st[-1]!=pair[c]: ok=False; break\n"
            "        st.pop()\n"
            'print("yes" if ok and not st else "no")\n'
        ),
        "cases": [
            {"name": "ok",  "stdin": "([{}])\n", "expected": "yes"},
            {"name": "no1", "stdin": "(]\n",     "expected": "no"},
            {"name": "no2", "stdin": "((()\n",   "expected": "no"},
            {"name": "deep","stdin": "{[()()]}\n","expected": "yes", "hidden": True},
        ],
    },
    {
        "slug": "py-merge-intervals",
        "title": "Merge intervals",
        "prompt": "Read N then N pairs `a b`. Print merged intervals, one per line, in ascending order.",
        "starter": "n = int(input())\nintervals = [tuple(map(int, input().split())) for _ in range(n)]\n",
        "ref": (
            "n=int(input()); xs=sorted(tuple(map(int,input().split())) for _ in range(n))\n"
            "out=[]\n"
            "for a,b in xs:\n"
            "    if out and a <= out[-1][1]: out[-1] = (out[-1][0], max(out[-1][1], b))\n"
            "    else: out.append((a,b))\n"
            'print("\\n".join(f"{a} {b}" for a,b in out))\n'
        ),
        "cases": [
            {"name": "basic", "stdin": "3\n1 3\n2 6\n8 10\n", "expected": "1 6\n8 10"},
            {"name": "touch", "stdin": "2\n1 4\n4 5\n",       "expected": "1 5"},
            {"name": "discrete", "stdin": "3\n1 2\n3 4\n5 6\n", "expected": "1 2\n3 4\n5 6", "hidden": True},
        ],
    },
    {
        "slug": "py-binary-search",
        "title": "Binary search",
        "prompt": "Read N then N sorted ints, then T. Print 0-based index of T or `-1`.",
        "starter": "n = int(input())\narr = [int(input()) for _ in range(n)]\ntarget = int(input())\n",
        "ref": (
            "import bisect\n"
            "n = int(input()); xs = [int(input()) for _ in range(n)]; t = int(input())\n"
            "i = bisect.bisect_left(xs, t)\n"
            'print(i if i < n and xs[i] == t else -1)\n'
        ),
        "cases": [
            {"name": "found",   "stdin": "5\n1\n2\n4\n7\n9\n7\n", "expected": "3"},
            {"name": "missing", "stdin": "4\n1\n3\n5\n7\n4\n",    "expected": "-1"},
            {"name": "first",   "stdin": "3\n1\n2\n3\n1\n",       "expected": "0", "hidden": True},
        ],
    },
    {
        "slug": "py-longest-substring",
        "title": "Longest substring without repeating chars",
        "prompt": "Read a string. Print the length of the longest substring with all distinct characters.",
        "starter": "s = input()\n",
        "ref": (
            "s = input(); seen = {}; best = 0; l = 0\n"
            "for r, c in enumerate(s):\n"
            "    if c in seen and seen[c] >= l: l = seen[c]+1\n"
            "    seen[c] = r; best = max(best, r-l+1)\n"
            "print(best)\n"
        ),
        "cases": [
            {"name": "abc", "stdin": "abcabcbb\n", "expected": "3"},
            {"name": "bb",  "stdin": "bbbbb\n",    "expected": "1"},
            {"name": "pwke", "stdin": "pwwkew\n",  "expected": "3", "hidden": True},
        ],
    },
    {
        "slug": "py-roman-to-int",
        "title": "Roman to integer",
        "prompt": "Read a Roman numeral (I,V,X,L,C,D,M; up to MMM). Print its decimal value.",
        "starter": "s = input()\n",
        "ref": (
            "v={'I':1,'V':5,'X':10,'L':50,'C':100,'D':500,'M':1000}\n"
            "s=input(); t=0; p=0\n"
            "for c in reversed(s):\n  x=v[c]\n  t+=x if x>=p else -x\n  p=x\nprint(t)\n"
        ),
        "cases": [
            {"name": "iii", "stdin": "III\n",  "expected": "3"},
            {"name": "iv",  "stdin": "IV\n",   "expected": "4"},
            {"name": "ix",  "stdin": "IX\n",   "expected": "9"},
            {"name": "mcmxciv", "stdin": "MCMXCIV\n", "expected": "1994", "hidden": True},
        ],
    },
    {
        "slug": "py-coin-change-min",
        "title": "Coin change (min coins)",
        "prompt": "Read M then M coin denominations, then target T. Print fewest coins to make T or `-1`.",
        "starter": "m = int(input())\ncoins = [int(input()) for _ in range(m)]\ntarget = int(input())\n",
        "ref": (
            "m=int(input()); coins=[int(input()) for _ in range(m)]; t=int(input())\n"
            "INF=10**9; dp=[0]+[INF]*t\n"
            "for i in range(1,t+1):\n  for c in coins:\n    if c<=i and dp[i-c]+1<dp[i]: dp[i]=dp[i-c]+1\n"
            "print(dp[t] if dp[t]<INF else -1)\n"
        ),
        "cases": [
            {"name": "11",  "stdin": "3\n1\n2\n5\n11\n", "expected": "3"},
            {"name": "imp", "stdin": "1\n2\n3\n",        "expected": "-1"},
            {"name": "13",  "stdin": "3\n1\n5\n10\n13\n","expected": "4", "hidden": True},
        ],
    },
    {
        "slug": "py-rotate-matrix",
        "title": "Rotate matrix 90°",
        "prompt": "Read N then N rows of N space-separated ints. Print rotated 90° clockwise (rows space-separated).",
        "starter": "n = int(input())\nmatrix = [list(map(int, input().split())) for _ in range(n)]\n",
        "ref": (
            "n=int(input()); m=[list(map(int,input().split())) for _ in range(n)]\n"
            "rot=[list(reversed(col)) for col in zip(*m)]\n"
            'print("\\n".join(" ".join(map(str,r)) for r in rot))\n'
        ),
        "cases": [
            {"name": "2x2", "stdin": "2\n1 2\n3 4\n", "expected": "3 1\n4 2"},
            {"name": "3x3", "stdin": "3\n1 2 3\n4 5 6\n7 8 9\n", "expected": "7 4 1\n8 5 2\n9 6 3", "hidden": True},
        ],
    },
    {
        "slug": "py-stock-profit",
        "title": "Best buy/sell once",
        "prompt": "Read N then N daily prices. Print the max profit from one buy + one later sell. 0 if no profit.",
        "starter": "n = int(input())\nprices = [int(input()) for _ in range(n)]\n",
        "ref": (
            "n=int(input()); xs=[int(input()) for _ in range(n)]\n"
            "lo=10**9; best=0\n"
            "for x in xs:\n  if x<lo: lo=x\n  best=max(best, x-lo)\n"
            "print(best)\n"
        ),
        "cases": [
            {"name": "ok",  "stdin": "6\n7\n1\n5\n3\n6\n4\n", "expected": "5"},
            {"name": "down","stdin": "5\n7\n6\n5\n4\n3\n",    "expected": "0"},
            {"name": "two", "stdin": "2\n2\n100\n",           "expected": "98", "hidden": True},
        ],
    },
    {
        "slug": "py-uniq-paths",
        "title": "Unique grid paths",
        "prompt": "Read M and N. Print count of unique paths from top-left to bottom-right (right/down only).",
        "starter": "m = int(input())\nn = int(input())\n",
        "ref": (
            "from math import comb\nm=int(input()); n=int(input())\nprint(comb(m+n-2, m-1))\n"
        ),
        "cases": [
            {"name": "3x7", "stdin": "3\n7\n", "expected": "28"},
            {"name": "3x2", "stdin": "3\n2\n", "expected": "3"},
            {"name": "1x1", "stdin": "1\n1\n", "expected": "1", "hidden": True},
        ],
    },
]

# ---------- WEB (HTML/CSS/JS — graded by iframe assertions) ----------
WEB_EASY = [
    {
        "slug": "web-hello-page",
        "title": "Hello page",
        "prompt": "Build an HTML page with one `<h1>` containing the text **Hello, web!**.",
        "starter": "<!DOCTYPE html>\n<html>\n<body>\n  <h1></h1>\n</body>\n</html>\n",
        "ref": "<h1>Hello, web!</h1>",
        "cases": [
            {"name": "has h1", "assertions": [
                {"kind": "selector", "selector": "h1"},
                {"kind": "text", "selector": "h1", "text": "Hello, web!"},
            ]},
        ],
    },
    {
        "slug": "web-list-of-3",
        "title": "Three-item list",
        "prompt": "Render a `<ul>` with exactly 3 `<li>` items.",
        "starter": "<ul>\n  <li></li>\n</ul>\n",
        "ref": "<ul><li>a</li><li>b</li><li>c</li></ul>",
        "cases": [
            {"name": "three li", "assertions": [
                {"kind": "count", "selector": "ul li", "count": 3},
            ]},
        ],
    },
    {
        "slug": "web-image-alt",
        "title": "Image with alt text",
        "prompt": "Add an `<img>` with attribute `alt=\"logo\"`.",
        "starter": "<img src=\"#\">\n",
        "ref": "<img src=\"#\" alt=\"logo\">",
        "cases": [
            {"name": "alt set", "assertions": [
                {"kind": "attr", "selector": "img", "attr": "alt", "value": "logo"},
            ]},
        ],
    },
    {
        "slug": "web-link-target-blank",
        "title": "Open in new tab",
        "prompt": "Add an `<a>` to `https://example.com` that opens in a new tab.",
        "starter": "<a href=\"\"></a>\n",
        "ref": "<a href=\"https://example.com\" target=\"_blank\">go</a>",
        "cases": [
            {"name": "href",   "assertions": [{"kind": "attr", "selector": "a", "attr": "href", "value": "https://example.com"}]},
            {"name": "target", "assertions": [{"kind": "attr", "selector": "a", "attr": "target", "value": "_blank"}]},
        ],
    },
    {
        "slug": "web-css-red-h1",
        "title": "Red headline",
        "prompt": "Make the `<h1>` red using CSS.",
        "starter": "<style>\n</style>\n<h1>Hello</h1>",
        "ref": "<style>h1{color:red}</style><h1>Hello</h1>",
        "cases": [
            {"name": "color is red", "assertions": [
                {"kind": "js", "expr": "getComputedStyle(document.querySelector('h1')).color === 'rgb(255, 0, 0)'"}
            ]},
        ],
    },
    {
        "slug": "web-button-id",
        "title": "Button by id",
        "prompt": "Render a `<button id=\"go\">` with text **Go**.",
        "starter": "<button></button>",
        "ref": "<button id=\"go\">Go</button>",
        "cases": [
            {"name": "id+text", "assertions": [
                {"kind": "selector", "selector": "#go"},
                {"kind": "text", "selector": "#go", "text": "Go"},
            ]},
        ],
    },
    {
        "slug": "web-form-input",
        "title": "Form with email input",
        "prompt": "Render a `<form>` containing one `<input type=\"email\" name=\"email\">`.",
        "starter": "<form>\n</form>",
        "ref": "<form><input type=\"email\" name=\"email\"></form>",
        "cases": [
            {"name": "email input", "assertions": [
                {"kind": "selector", "selector": "form input[type=email][name=email]"},
            ]},
        ],
    },
    {
        "slug": "web-flex-row",
        "title": "Flex row",
        "prompt": "Wrap two `<div>` siblings inside `.row` with display:flex (row).",
        "starter": "<div class=\"row\"><div></div><div></div></div>\n<style>\n</style>",
        "ref": "<style>.row{display:flex}</style><div class=\"row\"><div>a</div><div>b</div></div>",
        "cases": [
            {"name": "flex", "assertions": [
                {"kind": "js", "expr": "getComputedStyle(document.querySelector('.row')).display === 'flex'"}
            ]},
        ],
    },
    {
        "slug": "web-counter-button",
        "title": "Counter (JS)",
        "prompt": "Render `<button id=\"inc\">+1</button>` and `<span id=\"n\">0</span>`. Clicking the button increments the number.",
        "starter": "<button id=\"inc\">+1</button><span id=\"n\">0</span>\n<script>\n</script>",
        "ref": "<button id=\"inc\">+1</button><span id=\"n\">0</span><script>document.getElementById('inc').addEventListener('click',()=>{const s=document.getElementById('n');s.textContent=String(parseInt(s.textContent,10)+1)})</script>",
        "cases": [
            {"name": "click increments", "assertions": [
                {"kind": "js", "expr": "document.querySelector('#inc').click(); document.querySelector('#inc').click(); document.querySelector('#n').textContent === '2'"}
            ]},
        ],
    },
    {
        "slug": "web-grid-3-cols",
        "title": "Grid with three columns",
        "prompt": "Style `.grid` to be a CSS grid with 3 equal columns.",
        "starter": "<div class=\"grid\"><div></div><div></div><div></div></div>\n<style>\n</style>",
        "ref": "<style>.grid{display:grid;grid-template-columns:repeat(3,1fr)}</style>",
        "cases": [
            {"name": "grid", "assertions": [
                {"kind": "js", "expr": "getComputedStyle(document.querySelector('.grid')).display === 'grid'"},
                {"kind": "js", "expr": "getComputedStyle(document.querySelector('.grid')).gridTemplateColumns.split(' ').length === 3"}
            ]},
        ],
    },
]

WEB_MEDIUM = [
    {
        "slug": "web-toggle-class",
        "title": "Toggle a class",
        "prompt": "On click of `#tog`, toggle class `on` on `body`.",
        "starter": "<button id=\"tog\">toggle</button>\n<script>\n</script>",
        "ref": "<button id=\"tog\">toggle</button><script>document.getElementById('tog').onclick=()=>document.body.classList.toggle('on')</script>",
        "cases": [
            {"name": "toggle once",  "assertions": [{"kind": "js", "expr": "document.querySelector('#tog').click(); document.body.classList.contains('on')"}]},
            {"name": "toggle twice", "assertions": [{"kind": "js", "expr": "document.querySelector('#tog').click(); document.querySelector('#tog').click(); !document.body.classList.contains('on')"}]},
        ],
    },
    {
        "slug": "web-nav-bar",
        "title": "Top nav bar",
        "prompt": "Build a `<nav>` with three `<a>` children. The nav should be `display:flex` with `gap:1rem`.",
        "starter": "<nav>\n</nav>\n<style>\n</style>",
        "ref": "<style>nav{display:flex;gap:1rem}</style><nav><a href='#'>a</a><a href='#'>b</a><a href='#'>c</a></nav>",
        "cases": [
            {"name": "three links", "assertions": [{"kind": "count", "selector": "nav a", "count": 3}]},
            {"name": "flex+gap",    "assertions": [
                {"kind": "js", "expr": "getComputedStyle(document.querySelector('nav')).display === 'flex'"},
                {"kind": "js", "expr": "parseFloat(getComputedStyle(document.querySelector('nav')).gap) >= 15"}
            ]},
        ],
    },
    {
        "slug": "web-todo-add",
        "title": "Todo input → list",
        "prompt": "Form with `<input id=\"new\">` and `<button id=\"add\">Add</button>`. On click, append `<li>` containing the input value to `<ul id=\"todos\">`.",
        "starter": "<input id=\"new\"><button id=\"add\">Add</button><ul id=\"todos\"></ul>\n<script>\n</script>",
        "ref": "<input id='new'><button id='add'>Add</button><ul id='todos'></ul><script>document.getElementById('add').onclick=()=>{const v=document.getElementById('new').value;if(!v)return;const li=document.createElement('li');li.textContent=v;document.getElementById('todos').appendChild(li)}</script>",
        "cases": [
            {"name": "adds item", "assertions": [{"kind": "js", "expr": "const i=document.querySelector('#new'); i.value='task'; document.querySelector('#add').click(); document.querySelectorAll('#todos li').length === 1"}]},
        ],
    },
    {
        "slug": "web-form-validation",
        "title": "Required email",
        "prompt": "Render a form with input[type=email] required + a submit button.",
        "starter": "<form><input><button>Send</button></form>",
        "ref": "<form><input type='email' required><button>Send</button></form>",
        "cases": [
            {"name": "valid form HTML", "assertions": [
                {"kind": "selector", "selector": "form input[type=email][required]"},
                {"kind": "selector", "selector": "form button"},
            ]},
        ],
    },
    {
        "slug": "web-styled-card",
        "title": "Card style",
        "prompt": "`.card` has padding 16px, border-radius 8px, and background `#1a1a1a`.",
        "starter": "<div class=\"card\">hi</div>\n<style>\n</style>",
        "ref": "<style>.card{padding:16px;border-radius:8px;background:#1a1a1a;color:#fff}</style><div class='card'>hi</div>",
        "cases": [
            {"name": "padding", "assertions": [{"kind": "js", "expr": "parseFloat(getComputedStyle(document.querySelector('.card')).padding) === 16"}]},
            {"name": "radius",  "assertions": [{"kind": "js", "expr": "parseFloat(getComputedStyle(document.querySelector('.card')).borderRadius) === 8"}]},
            {"name": "bg",      "assertions": [{"kind": "js", "expr": "getComputedStyle(document.querySelector('.card')).backgroundColor === 'rgb(26, 26, 26)'"}]},
        ],
    },
    {
        "slug": "web-input-mirror",
        "title": "Input mirror",
        "prompt": "Typing into `#src` should mirror to `#out` text in real time.",
        "starter": "<input id=\"src\"><div id=\"out\"></div>\n<script>\n</script>",
        "ref": "<input id='src'><div id='out'></div><script>const s=document.getElementById('src'),o=document.getElementById('out');s.addEventListener('input',()=>o.textContent=s.value)</script>",
        "cases": [
            {"name": "mirrors", "assertions": [{"kind": "js", "expr": "const i=document.querySelector('#src'); i.value='hi'; i.dispatchEvent(new Event('input')); document.querySelector('#out').textContent === 'hi'"}]},
        ],
    },
    {
        "slug": "web-tabs",
        "title": "Tabs",
        "prompt": "Two buttons `.tab[data-id]` and two panels `.panel[data-id]`. Clicking a tab shows only its panel (others get `hidden` attribute).",
        "starter": "<button class='tab' data-id='a'>A</button><button class='tab' data-id='b'>B</button><div class='panel' data-id='a'>A!</div><div class='panel' data-id='b'>B!</div>\n<script>\n</script>",
        "ref": "<button class='tab' data-id='a'>A</button><button class='tab' data-id='b'>B</button><div class='panel' data-id='a'>A!</div><div class='panel' data-id='b'>B!</div><script>document.querySelectorAll('.tab').forEach(t=>t.addEventListener('click',()=>{document.querySelectorAll('.panel').forEach(p=>p.toggleAttribute('hidden', p.dataset.id !== t.dataset.id))}))</script>",
        "cases": [
            {"name": "switches", "assertions": [
                {"kind": "js", "expr": "document.querySelector('.tab[data-id=b]').click(); document.querySelector('.panel[data-id=a]').hasAttribute('hidden') && !document.querySelector('.panel[data-id=b]').hasAttribute('hidden')"}
            ]},
        ],
    },
    {
        "slug": "web-clamp-text",
        "title": "Clamp two-lines",
        "prompt": "Apply CSS to `.bio` so it shows max 2 lines and ellipses (use `-webkit-line-clamp` family).",
        "starter": "<p class='bio'>long long long very long bio</p>\n<style>\n</style>",
        "ref": "<style>.bio{display:-webkit-box;-webkit-line-clamp:2;-webkit-box-orient:vertical;overflow:hidden}</style>",
        "cases": [
            {"name": "clamp",  "assertions": [
                {"kind": "js", "expr": "getComputedStyle(document.querySelector('.bio')).webkitLineClamp == '2' || getComputedStyle(document.querySelector('.bio')).getPropertyValue('-webkit-line-clamp') === '2'"}
            ]},
        ],
    },
    {
        "slug": "web-modal",
        "title": "Modal open/close",
        "prompt": "`#open` shows `<dialog id=\"m\">`. `#close` (inside the dialog) closes it.",
        "starter": "<button id='open'>open</button><dialog id='m'><button id='close'>x</button></dialog>\n<script>\n</script>",
        "ref": "<button id='open'>open</button><dialog id='m'><button id='close'>x</button></dialog><script>document.getElementById('open').onclick=()=>document.getElementById('m').showModal();document.getElementById('close').onclick=()=>document.getElementById('m').close()</script>",
        "cases": [
            {"name": "opens",  "assertions": [{"kind": "js", "expr": "document.querySelector('#open').click(); document.querySelector('#m').open"}]},
            {"name": "closes", "assertions": [{"kind": "js", "expr": "document.querySelector('#open').click(); document.querySelector('#close').click(); !document.querySelector('#m').open"}]},
        ],
    },
    {
        "slug": "web-search-filter",
        "title": "Live search filter",
        "prompt": "Typing in `#q` hides `<li>` whose textContent doesn't contain the input value (case-insensitive).",
        "starter": "<input id='q'><ul><li>Apple</li><li>Banana</li><li>Cherry</li></ul>\n<script>\n</script>",
        "ref": "<input id='q'><ul><li>Apple</li><li>Banana</li><li>Cherry</li></ul><script>document.getElementById('q').addEventListener('input',e=>{const v=e.target.value.toLowerCase();document.querySelectorAll('li').forEach(li=>{li.style.display=li.textContent.toLowerCase().includes(v)?'':'none'})})</script>",
        "cases": [
            {"name": "filters", "assertions": [
                {"kind": "js", "expr": "const q=document.querySelector('#q'); q.value='ban'; q.dispatchEvent(new Event('input')); Array.from(document.querySelectorAll('li')).filter(li=>li.style.display!=='none').length === 1"}
            ]},
        ],
    },
]

WEB_HARD = [
    {
        "slug": "web-debounced-search",
        "title": "Debounced search",
        "prompt": "Implement a 200 ms debounce: typing into `#q` should set `#out`'s text to the input only after the user pauses for 200 ms.",
        "starter": "<input id='q'><div id='out'></div>\n<script>\n</script>",
        "ref": "<input id='q'><div id='out'></div><script>let t;document.getElementById('q').addEventListener('input',e=>{clearTimeout(t);t=setTimeout(()=>{document.getElementById('out').textContent=e.target.value},200)})</script>",
        "cases": [
            {"name": "debounces", "assertions": [
                {"kind": "js", "expr": "const q=document.querySelector('#q'); q.value='hi'; q.dispatchEvent(new Event('input')); document.querySelector('#out').textContent !== 'hi'"}
            ]},
        ],
    },
    {
        "slug": "web-sortable-table",
        "title": "Sortable column",
        "prompt": "Click `<th data-sort>` to sort the table rows ascending by that column's text.",
        "starter": "<table><thead><tr><th data-sort>Name</th></tr></thead><tbody><tr><td>Charlie</td></tr><tr><td>Alpha</td></tr><tr><td>Bravo</td></tr></tbody></table>\n<script>\n</script>",
        "ref": "<script>document.querySelector('th[data-sort]').addEventListener('click',()=>{const tb=document.querySelector('tbody');const rows=Array.from(tb.querySelectorAll('tr'));rows.sort((a,b)=>a.cells[0].textContent.localeCompare(b.cells[0].textContent));rows.forEach(r=>tb.appendChild(r))})</script>",
        "cases": [
            {"name": "sorted", "assertions": [
                {"kind": "js", "expr": "document.querySelector('th[data-sort]').click(); const cs=Array.from(document.querySelectorAll('tbody td')).map(td=>td.textContent); cs[0]==='Alpha'&&cs[1]==='Bravo'&&cs[2]==='Charlie'"}
            ]},
        ],
    },
    {
        "slug": "web-tic-tac-toe-grid",
        "title": "Tic-tac-toe grid",
        "prompt": "9 buttons inside `#board` arranged 3 cols. Clicking a button writes `X` into its `data-mark`.",
        "starter": "<div id='board'></div>\n<script>\n</script>\n<style>\n</style>",
        "ref": "<style>#board{display:grid;grid-template-columns:repeat(3,1fr);gap:4px}</style><div id='board'></div><script>const b=document.getElementById('board');for(let i=0;i<9;i++){const btn=document.createElement('button');btn.dataset.mark='';btn.addEventListener('click',()=>btn.dataset.mark='X');b.appendChild(btn)}</script>",
        "cases": [
            {"name": "9 buttons", "assertions": [{"kind": "count", "selector": "#board button", "count": 9}]},
            {"name": "3 cols",    "assertions": [{"kind": "js", "expr": "getComputedStyle(document.querySelector('#board')).gridTemplateColumns.split(' ').length === 3"}]},
            {"name": "click marks", "assertions": [{"kind": "js", "expr": "const b=document.querySelector('#board button'); b.click(); b.dataset.mark === 'X'"}]},
        ],
    },
    {
        "slug": "web-fetch-mock",
        "title": "Fetch + render",
        "prompt": "Override `window.fetch` to return `[{name:'A'},{name:'B'}]`. On `#load` click, render names as `<li>` inside `<ul>`.",
        "starter": "<button id='load'>load</button><ul></ul>\n<script>\nwindow.fetch = () => Promise.resolve({ json: () => Promise.resolve([{name:'A'},{name:'B'}]) });\n</script>",
        "ref": "<button id='load'>load</button><ul></ul><script>window.fetch = () => Promise.resolve({ json: () => Promise.resolve([{name:'A'},{name:'B'}]) });document.getElementById('load').onclick=async()=>{const r=await fetch();const d=await r.json();const ul=document.querySelector('ul');d.forEach(x=>{const li=document.createElement('li');li.textContent=x.name;ul.appendChild(li)})}</script>",
        "cases": [
            {"name": "renders", "assertions": [
                {"kind": "js", "expr": "(async () => { document.querySelector('#load').click(); await new Promise(r => setTimeout(r, 30)); return document.querySelectorAll('ul li').length === 2; })()"}
            ]},
        ],
    },
    {
        "slug": "web-drag-reorder",
        "title": "Drag-reorder list (HTML5 DnD)",
        "prompt": "Make `<li draggable>` items reorderable: dragstart stores index, drop appends before target.",
        "starter": "<ul id='l'><li draggable='true'>A</li><li draggable='true'>B</li><li draggable='true'>C</li></ul>\n<script>\n</script>",
        "ref": "<ul id='l'><li draggable='true'>A</li><li draggable='true'>B</li><li draggable='true'>C</li></ul><script>let dragged;document.querySelectorAll('li').forEach(li=>{li.addEventListener('dragstart',e=>{dragged=li});li.addEventListener('dragover',e=>e.preventDefault());li.addEventListener('drop',e=>{e.preventDefault();li.parentNode.insertBefore(dragged,li)})})</script>",
        "cases": [
            {"name": "draggable set", "assertions": [{"kind": "count", "selector": "li[draggable]", "count": 3}]},
        ],
    },
    {
        "slug": "web-form-error-state",
        "title": "Inline form errors",
        "prompt": "On submit of `#f`, if `#email` is invalid, add class `err` to it; if valid, add class `ok` instead.",
        "starter": "<form id='f'><input id='email' type='email'><button>go</button></form>\n<script>\n</script>",
        "ref": "<script>document.getElementById('f').addEventListener('submit',e=>{e.preventDefault();const i=document.getElementById('email');i.classList.toggle('err',!i.checkValidity());i.classList.toggle('ok',i.checkValidity())})</script>",
        "cases": [
            {"name": "ok-class", "assertions": [
                {"kind": "js", "expr": "const i=document.querySelector('#email'); i.value='a@b.co'; document.querySelector('#f').dispatchEvent(new Event('submit')); i.classList.contains('ok')"}
            ]},
            {"name": "err-class", "assertions": [
                {"kind": "js", "expr": "const i=document.querySelector('#email'); i.value='nope'; document.querySelector('#f').dispatchEvent(new Event('submit')); i.classList.contains('err')"}
            ]},
        ],
    },
    {
        "slug": "web-counter-localstorage",
        "title": "Persistent counter",
        "prompt": "`#inc` button increments `#n`. The current value persists in `localStorage` under key `count`.",
        "starter": "<button id='inc'>+</button><span id='n'>0</span>\n<script>\n</script>",
        "ref": "<button id='inc'>+</button><span id='n'>0</span><script>const k='count';const n=document.getElementById('n');n.textContent=localStorage.getItem(k)||'0';document.getElementById('inc').onclick=()=>{const v=String((+n.textContent)+1);n.textContent=v;localStorage.setItem(k,v)}</script>",
        "cases": [
            {"name": "saves to ls", "assertions": [
                {"kind": "js", "expr": "document.querySelector('#inc').click(); localStorage.getItem('count') === '1'"}
            ]},
        ],
    },
    {
        "slug": "web-dark-mode",
        "title": "Dark mode toggle",
        "prompt": "`#dark` toggles class `dark` on `<html>`. With `dark`, `body` background must be `#000`.",
        "starter": "<button id='dark'>dark</button>\n<style>\n</style>\n<script>\n</script>",
        "ref": "<style>html.dark body{background:#000}</style><button id='dark'>dark</button><script>document.getElementById('dark').onclick=()=>document.documentElement.classList.toggle('dark')</script>",
        "cases": [
            {"name": "toggles class", "assertions": [{"kind": "js", "expr": "document.querySelector('#dark').click(); document.documentElement.classList.contains('dark')"}]},
            {"name": "bg goes black",  "assertions": [{"kind": "js", "expr": "document.querySelector('#dark').click(); getComputedStyle(document.body).backgroundColor === 'rgb(0, 0, 0)'"}]},
        ],
    },
    {
        "slug": "web-keyboard-shortcut",
        "title": "Keyboard shortcut",
        "prompt": "Pressing the **/** key (anywhere except in inputs) focuses `#search`.",
        "starter": "<input id='search'>\n<script>\n</script>",
        "ref": "<input id='search'><script>document.addEventListener('keydown',e=>{if(e.key==='/' && !['INPUT','TEXTAREA'].includes(document.activeElement.tagName)){e.preventDefault();document.getElementById('search').focus()}})</script>",
        "cases": [
            {"name": "focuses on /", "assertions": [
                {"kind": "js", "expr": "document.body.dispatchEvent(new KeyboardEvent('keydown',{key:'/',bubbles:true})); document.activeElement.id === 'search'"}
            ]},
        ],
    },
    {
        "slug": "web-rgb-to-hex",
        "title": "RGB → Hex",
        "prompt": "Define `window.rgbToHex(r,g,b)` returning `#rrggbb` (lowercase, two-digit).",
        "starter": "<script>\n</script>",
        "ref": "<script>window.rgbToHex=(r,g,b)=>'#'+[r,g,b].map(x=>x.toString(16).padStart(2,'0')).join('')</script>",
        "cases": [
            {"name": "white", "assertions": [{"kind": "js", "expr": "window.rgbToHex(255,255,255) === '#ffffff'"}]},
            {"name": "mid",   "assertions": [{"kind": "js", "expr": "window.rgbToHex(15,16,17)    === '#0f1011'"}]},
            {"name": "black", "assertions": [{"kind": "js", "expr": "window.rgbToHex(0,0,0)       === '#000000'"}]},
        ],
    },
]


PY_EASY_2 = [
    {
        "slug": "py-abs-value",
        "title": "Absolute value",
        "prompt": "Read an integer. Print its absolute value.",
        "starter": "n = int(input())\n",
        "ref": "print(abs(int(input())))\n",
        "cases": [
            {"name": "pos",  "stdin": "5\n",  "expected": "5"},
            {"name": "neg",  "stdin": "-3\n", "expected": "3"},
            {"name": "zero", "stdin": "0\n",  "expected": "0", "hidden": True},
        ],
    },
    {
        "slug": "py-multiply-two",
        "title": "Multiply two numbers",
        "prompt": "Read two integers (one per line). Print their product.",
        "starter": "a = int(input())\nb = int(input())\n",
        "ref": "print(int(input()) * int(input()))\n",
        "cases": [
            {"name": "basic", "stdin": "3\n4\n",   "expected": "12"},
            {"name": "zero",  "stdin": "0\n99\n",  "expected": "0"},
            {"name": "neg",   "stdin": "-5\n3\n",  "expected": "-15", "hidden": True},
        ],
    },
    {
        "slug": "py-celsius-to-fahrenheit",
        "title": "Celsius to Fahrenheit",
        "prompt": "Read a float C. Print the Fahrenheit equivalent as a float with 2 decimal places.",
        "starter": "c = float(input())\n",
        "ref": "c = float(input())\nprint(f\"{c * 9/5 + 32:.2f}\")\n",
        "cases": [
            {"name": "zero",    "stdin": "0\n",   "expected": "32.00"},
            {"name": "hundred", "stdin": "100\n", "expected": "212.00"},
            {"name": "body",    "stdin": "37\n",  "expected": "98.60", "hidden": True},
        ],
    },
    {
        "slug": "py-digit-sum",
        "title": "Sum of digits",
        "prompt": "Read a non-negative integer. Print the sum of its digits.",
        "starter": "n = input().strip()\n",
        "ref": "print(sum(int(d) for d in input().strip()))\n",
        "cases": [
            {"name": "123",  "stdin": "123\n",  "expected": "6"},
            {"name": "0",    "stdin": "0\n",    "expected": "0"},
            {"name": "9999", "stdin": "9999\n", "expected": "36", "hidden": True},
        ],
    },
    {
        "slug": "py-to-uppercase",
        "title": "Uppercase string",
        "prompt": "Read a line. Print it in uppercase.",
        "starter": "s = input()\n",
        "ref": "print(input().upper())\n",
        "cases": [
            {"name": "lower",  "stdin": "hello\n", "expected": "HELLO"},
            {"name": "mixed",  "stdin": "HeLLo\n", "expected": "HELLO"},
            {"name": "digits", "stdin": "abc123\n","expected": "ABC123", "hidden": True},
        ],
    },
    {
        "slug": "py-is-divisible",
        "title": "Divisibility check",
        "prompt": "Read N then D. Print `yes` if N is divisible by D, else `no`.",
        "starter": "n = int(input())\nd = int(input())\n",
        "ref": 'n,d=int(input()),int(input())\nprint("yes" if n%d==0 else "no")\n',
        "cases": [
            {"name": "yes",  "stdin": "10\n5\n", "expected": "yes"},
            {"name": "no",   "stdin": "7\n3\n",  "expected": "no"},
            {"name": "neg",  "stdin": "-6\n3\n", "expected": "yes", "hidden": True},
        ],
    },
    {
        "slug": "py-count-char",
        "title": "Count a character",
        "prompt": "Read a string on line 1, a single character on line 2. Print how many times the character appears (case-sensitive).",
        "starter": "s = input()\nc = input()\n",
        "ref": "s=input();c=input();print(s.count(c))\n",
        "cases": [
            {"name": "basic", "stdin": "hello\nl\n",  "expected": "2"},
            {"name": "none",  "stdin": "abc\nz\n",    "expected": "0"},
            {"name": "all",   "stdin": "aaaa\na\n",   "expected": "4", "hidden": True},
        ],
    },
    {
        "slug": "py-repeat-string",
        "title": "Repeat a string",
        "prompt": "Read a string S then integer N. Print S repeated N times (no separator).",
        "starter": "s = input()\nn = int(input())\n",
        "ref": "s=input();n=int(input());print(s*n)\n",
        "cases": [
            {"name": "ab3",  "stdin": "ab\n3\n", "expected": "ababab"},
            {"name": "x1",   "stdin": "x\n1\n",  "expected": "x"},
            {"name": "hi0",  "stdin": "hi\n0\n", "expected": "", "hidden": True},
        ],
    },
    {
        "slug": "py-longest-word",
        "title": "Longest word",
        "prompt": "Read a line of space-separated words. Print the longest word. If tied, print the first.",
        "starter": "words = input().split()\n",
        "ref": "ws=input().split();print(max(ws,key=len))\n",
        "cases": [
            {"name": "basic", "stdin": "the quick brown fox\n", "expected": "quick"},
            {"name": "tie",   "stdin": "ab cd ef\n",            "expected": "ab"},
            {"name": "one",   "stdin": "hello\n",               "expected": "hello", "hidden": True},
        ],
    },
    {
        "slug": "py-remove-spaces",
        "title": "Remove spaces",
        "prompt": "Read a line. Print it with all spaces removed.",
        "starter": "s = input()\n",
        "ref": 'print(input().replace(" ",""))\n',
        "cases": [
            {"name": "basic",  "stdin": "hello world\n",  "expected": "helloworld"},
            {"name": "multi",  "stdin": "a b  c\n",       "expected": "abc"},
            {"name": "none",   "stdin": "abc\n",          "expected": "abc", "hidden": True},
        ],
    },
    {
        "slug": "py-title-case",
        "title": "Title case",
        "prompt": "Read a line. Print it in title case (first letter of each word capitalised).",
        "starter": "s = input()\n",
        "ref": "print(input().title())\n",
        "cases": [
            {"name": "basic",  "stdin": "hello world\n",        "expected": "Hello World"},
            {"name": "upper",  "stdin": "HELLO WORLD\n",        "expected": "Hello World"},
            {"name": "mixed",  "stdin": "the quick fox\n",      "expected": "The Quick Fox", "hidden": True},
        ],
    },
    {
        "slug": "py-power",
        "title": "Power",
        "prompt": "Read base B and exponent E (both integers, E ≥ 0). Print B**E.",
        "starter": "base = int(input())\nexp = int(input())\n",
        "ref": "b=int(input());e=int(input());print(b**e)\n",
        "cases": [
            {"name": "2-10", "stdin": "2\n10\n", "expected": "1024"},
            {"name": "5-0",  "stdin": "5\n0\n",  "expected": "1"},
            {"name": "3-3",  "stdin": "3\n3\n",  "expected": "27", "hidden": True},
        ],
    },
    {
        "slug": "py-average-list",
        "title": "Average of list",
        "prompt": "Read N then N floats. Print their average with 2 decimal places.",
        "starter": "n = int(input())\nnumbers = [float(input()) for _ in range(n)]\n",
        "ref": "n=int(input());xs=[float(input()) for _ in range(n)];print(f\"{sum(xs)/n:.2f}\")\n",
        "cases": [
            {"name": "ints",  "stdin": "3\n1\n2\n3\n",      "expected": "2.00"},
            {"name": "float", "stdin": "2\n1.5\n2.5\n",     "expected": "2.00"},
            {"name": "one",   "stdin": "1\n7\n",            "expected": "7.00", "hidden": True},
        ],
    },
    {
        "slug": "py-is-positive",
        "title": "Positive, negative, or zero",
        "prompt": "Read an integer. Print `positive`, `negative`, or `zero`.",
        "starter": "n = int(input())\n",
        "ref": 'n=int(input())\nprint("positive" if n>0 else "negative" if n<0 else "zero")\n',
        "cases": [
            {"name": "pos",  "stdin": "5\n",  "expected": "positive"},
            {"name": "neg",  "stdin": "-3\n", "expected": "negative"},
            {"name": "zero", "stdin": "0\n",  "expected": "zero", "hidden": True},
        ],
    },
    {
        "slug": "py-first-last-char",
        "title": "First and last character",
        "prompt": "Read a non-empty string. Print the first and last character separated by a space.",
        "starter": "s = input()\n",
        "ref": "s=input();print(s[0],s[-1])\n",
        "cases": [
            {"name": "hello",  "stdin": "hello\n", "expected": "h o"},
            {"name": "single", "stdin": "x\n",     "expected": "x x"},
            {"name": "long",   "stdin": "abcdef\n","expected": "a f", "hidden": True},
        ],
    },
    {
        "slug": "py-rectangle-area",
        "title": "Rectangle area",
        "prompt": "Read width and height (integers). Print the area.",
        "starter": "width = int(input())\nheight = int(input())\n",
        "ref": "print(int(input())*int(input()))\n",
        "cases": [
            {"name": "3x4",  "stdin": "3\n4\n",  "expected": "12"},
            {"name": "1x1",  "stdin": "1\n1\n",  "expected": "1"},
            {"name": "10x7", "stdin": "10\n7\n", "expected": "70", "hidden": True},
        ],
    },
    {
        "slug": "py-count-to-n",
        "title": "Count to N",
        "prompt": "Read N. Print integers from 1 to N inclusive, one per line.",
        "starter": "n = int(input())\n",
        "ref": "n=int(input())\nfor i in range(1,n+1):print(i)\n",
        "cases": [
            {"name": "n5", "stdin": "5\n", "expected": "1\n2\n3\n4\n5"},
            {"name": "n1", "stdin": "1\n", "expected": "1"},
            {"name": "n3", "stdin": "3\n", "expected": "1\n2\n3", "hidden": True},
        ],
    },
    {
        "slug": "py-min-max",
        "title": "Min and max",
        "prompt": "Read N then N integers. Print the minimum and maximum separated by a space.",
        "starter": "n = int(input())\nnumbers = [int(input()) for _ in range(n)]\n",
        "ref": "n=int(input());xs=[int(input()) for _ in range(n)];print(min(xs),max(xs))\n",
        "cases": [
            {"name": "basic",  "stdin": "4\n3\n1\n4\n2\n", "expected": "1 4"},
            {"name": "same",   "stdin": "3\n5\n5\n5\n",    "expected": "5 5"},
            {"name": "neg",    "stdin": "3\n-1\n0\n1\n",   "expected": "-1 1", "hidden": True},
        ],
    },
    {
        "slug": "py-sum-even",
        "title": "Sum of evens",
        "prompt": "Read N then N integers. Print the sum of the even ones.",
        "starter": "n = int(input())\nnumbers = [int(input()) for _ in range(n)]\n",
        "ref": "n=int(input());xs=[int(input()) for _ in range(n)];print(sum(x for x in xs if x%2==0))\n",
        "cases": [
            {"name": "basic",  "stdin": "5\n1\n2\n3\n4\n5\n", "expected": "6"},
            {"name": "none",   "stdin": "3\n1\n3\n5\n",        "expected": "0"},
            {"name": "all",    "stdin": "3\n2\n4\n6\n",        "expected": "12", "hidden": True},
        ],
    },
    {
        "slug": "py-string-length",
        "title": "String length",
        "prompt": "Read a line. Print its length.",
        "starter": "s = input()\n",
        "ref": "print(len(input()))\n",
        "cases": [
            {"name": "hello", "stdin": "hello\n", "expected": "5"},
            {"name": "empty", "stdin": "\n",      "expected": "0"},
            {"name": "space", "stdin": "a b\n",   "expected": "3", "hidden": True},
        ],
    },
    {
        "slug": "py-number-parity-list",
        "title": "Split even/odd",
        "prompt": "Read N then N integers. Print all evens (ascending) then all odds (ascending), each group space-separated on its own line. If a group is empty print an empty line.",
        "starter": "n = int(input())\nnumbers = [int(input()) for _ in range(n)]\n",
        "ref": (
            "n=int(input()); xs=[int(input()) for _ in range(n)]\n"
            "evens=sorted(x for x in xs if x%2==0)\n"
            "odds=sorted(x for x in xs if x%2!=0)\n"
            'print(" ".join(map(str,evens)))\nprint(" ".join(map(str,odds)))\n'
        ),
        "cases": [
            {"name": "mixed", "stdin": "5\n1\n2\n3\n4\n5\n", "expected": "2 4\n1 3 5"},
            {"name": "all-odd","stdin": "3\n1\n3\n5\n",       "expected": "\n1 3 5"},
            {"name": "all-even","stdin": "2\n4\n2\n",         "expected": "2 4\n", "hidden": True},
        ],
    },
    {
        "slug": "py-divisors",
        "title": "List divisors",
        "prompt": "Read a positive integer N. Print all divisors of N in ascending order, one per line.",
        "starter": "n = int(input())\n",
        "ref": "n=int(input())\nfor i in range(1,n+1):\n    if n%i==0:print(i)\n",
        "cases": [
            {"name": "12", "stdin": "12\n", "expected": "1\n2\n3\n4\n6\n12"},
            {"name": "7",  "stdin": "7\n",  "expected": "1\n7"},
            {"name": "1",  "stdin": "1\n",  "expected": "1", "hidden": True},
        ],
    },
    {
        "slug": "py-lowercase",
        "title": "Lowercase string",
        "prompt": "Read a line. Print it in lowercase.",
        "starter": "s = input()\n",
        "ref": "print(input().lower())\n",
        "cases": [
            {"name": "upper", "stdin": "HELLO\n",   "expected": "hello"},
            {"name": "mixed", "stdin": "PyThOn\n",  "expected": "python"},
            {"name": "num",   "stdin": "A1B2\n",    "expected": "a1b2", "hidden": True},
        ],
    },
]

PY_MEDIUM_2 = [
    {
        "slug": "py-missing-number",
        "title": "Missing number",
        "prompt": "Read N then N-1 distinct integers from 1 to N (one per line). Print the missing one.",
        "starter": "n = int(input())\nnumbers = [int(input()) for _ in range(n - 1)]\n",
        "ref": "n=int(input());s=sum(int(input()) for _ in range(n-1));print(n*(n+1)//2-s)\n",
        "cases": [
            {"name": "basic",  "stdin": "5\n1\n2\n4\n5\n", "expected": "3"},
            {"name": "first",  "stdin": "3\n2\n3\n",        "expected": "1"},
            {"name": "last",   "stdin": "4\n1\n2\n3\n",     "expected": "4", "hidden": True},
        ],
    },
    {
        "slug": "py-decimal-to-binary",
        "title": "Decimal to binary",
        "prompt": "Read a non-negative integer. Print its binary representation (no `0b` prefix).",
        "starter": "n = int(input())\n",
        "ref": "n=int(input());print(bin(n)[2:])\n",
        "cases": [
            {"name": "ten",  "stdin": "10\n", "expected": "1010"},
            {"name": "zero", "stdin": "0\n",  "expected": "0"},
            {"name": "255",  "stdin": "255\n","expected": "11111111", "hidden": True},
        ],
    },
    {
        "slug": "py-caesar-cipher",
        "title": "Caesar cipher",
        "prompt": "Read a string S then shift K (0-25). Rotate letters by K (preserve case, keep non-alpha unchanged). Print result.",
        "starter": "s = input()\nk = int(input())\n",
        "ref": (
            "s=input();k=int(input())\n"
            "out=[]\n"
            "for c in s:\n"
            "    if c.isalpha():\n"
            "        b=ord('A') if c.isupper() else ord('a')\n"
            "        out.append(chr((ord(c)-b+k)%26+b))\n"
            "    else: out.append(c)\n"
            'print("".join(out))\n'
        ),
        "cases": [
            {"name": "abc3",  "stdin": "abc\n3\n",   "expected": "def"},
            {"name": "xyz3",  "stdin": "xyz\n3\n",   "expected": "abc"},
            {"name": "mixed", "stdin": "Hello!\n13\n","expected": "Uryyb!", "hidden": True},
        ],
    },
    {
        "slug": "py-remove-duplicates",
        "title": "Remove duplicates",
        "prompt": "Read N then N integers. Print them with duplicates removed, preserving first-occurrence order, one per line.",
        "starter": "n = int(input())\nnumbers = [int(input()) for _ in range(n)]\n",
        "ref": "n=int(input());seen=set();xs=[int(input()) for _ in range(n)]\nfor x in xs:\n    if x not in seen:print(x);seen.add(x)\n",
        "cases": [
            {"name": "basic", "stdin": "5\n1\n2\n1\n3\n2\n", "expected": "1\n2\n3"},
            {"name": "all",   "stdin": "3\n5\n5\n5\n",        "expected": "5"},
            {"name": "none",  "stdin": "3\n1\n2\n3\n",        "expected": "1\n2\n3", "hidden": True},
        ],
    },
    {
        "slug": "py-rotate-list",
        "title": "Rotate list left",
        "prompt": "Read N then N integers then K. Print the list rotated left by K positions, space-separated.",
        "starter": "n = int(input())\narr = [int(input()) for _ in range(n)]\nk = int(input())\n",
        "ref": "n=int(input());xs=[int(input()) for _ in range(n)];k=int(input());k%=max(n,1);print(*xs[k:]+xs[:k])\n",
        "cases": [
            {"name": "basic",  "stdin": "5\n1\n2\n3\n4\n5\n2\n", "expected": "3 4 5 1 2"},
            {"name": "zero",   "stdin": "3\n1\n2\n3\n0\n",        "expected": "1 2 3"},
            {"name": "full",   "stdin": "3\n1\n2\n3\n3\n",        "expected": "1 2 3", "hidden": True},
        ],
    },
    {
        "slug": "py-max-subarray",
        "title": "Maximum subarray sum",
        "prompt": "Read N then N integers. Print the maximum contiguous subarray sum (Kadane's).",
        "starter": "n = int(input())\nnumbers = [int(input()) for _ in range(n)]\n",
        "ref": (
            "n=int(input());xs=[int(input()) for _ in range(n)]\n"
            "best=cur=xs[0]\n"
            "for x in xs[1:]:\n  cur=max(x,cur+x);best=max(best,cur)\n"
            "print(best)\n"
        ),
        "cases": [
            {"name": "basic", "stdin": "8\n-2\n1\n-3\n4\n-1\n2\n1\n-5\n", "expected": "6"},
            {"name": "all-neg","stdin": "3\n-3\n-1\n-2\n",                 "expected": "-1"},
            {"name": "single", "stdin": "1\n7\n",                          "expected": "7", "hidden": True},
        ],
    },
    {
        "slug": "py-count-freq",
        "title": "Character frequency",
        "prompt": "Read a string. Print each character and its count, sorted by character, one per line as `char:count`.",
        "starter": "s = input()\n",
        "ref": (
            "from collections import Counter\n"
            "s=input();c=Counter(s)\n"
            'print("\\n".join(f"{k}:{v}" for k,v in sorted(c.items())))\n'
        ),
        "cases": [
            {"name": "basic",  "stdin": "aabbc\n", "expected": "a:2\nb:2\nc:1"},
            {"name": "single", "stdin": "z\n",     "expected": "z:1"},
            {"name": "mixed",  "stdin": "abcabc\n","expected": "a:2\nb:2\nc:2", "hidden": True},
        ],
    },
    {
        "slug": "py-transpose-matrix",
        "title": "Transpose matrix",
        "prompt": "Read N then N rows of N space-separated integers. Print the transposed matrix (rows space-separated).",
        "starter": "n = int(input())\nmatrix = [list(map(int, input().split())) for _ in range(n)]\n",
        "ref": (
            "n=int(input());m=[list(map(int,input().split())) for _ in range(n)]\n"
            'print("\\n".join(" ".join(map(str,r)) for r in zip(*m)))\n'
        ),
        "cases": [
            {"name": "2x2", "stdin": "2\n1 2\n3 4\n",        "expected": "1 3\n2 4"},
            {"name": "3x3", "stdin": "3\n1 2 3\n4 5 6\n7 8 9\n","expected": "1 4 7\n2 5 8\n3 6 9", "hidden": True},
        ],
    },
    {
        "slug": "py-is-sorted",
        "title": "Is list sorted?",
        "prompt": "Read N then N integers. Print `yes` if non-decreasing, else `no`.",
        "starter": "n = int(input())\nnumbers = [int(input()) for _ in range(n)]\n",
        "ref": "n=int(input());xs=[int(input()) for _ in range(n)];print('yes' if xs==sorted(xs) else 'no')\n",
        "cases": [
            {"name": "yes",  "stdin": "4\n1\n2\n2\n3\n", "expected": "yes"},
            {"name": "no",   "stdin": "3\n3\n1\n2\n",    "expected": "no"},
            {"name": "one",  "stdin": "1\n5\n",           "expected": "yes", "hidden": True},
        ],
    },
    {
        "slug": "py-chunk-list",
        "title": "Chunk list",
        "prompt": "Read N, then N integers, then chunk size K. Print chunks (space-separated) one per line.",
        "starter": "n = int(input())\nnumbers = [int(input()) for _ in range(n)]\nk = int(input())\n",
        "ref": (
            "n=int(input());xs=[int(input()) for _ in range(n)];k=int(input())\n"
            'print("\\n".join(" ".join(map(str,xs[i:i+k])) for i in range(0,n,k)))\n'
        ),
        "cases": [
            {"name": "basic", "stdin": "5\n1\n2\n3\n4\n5\n2\n", "expected": "1 2\n3 4\n5"},
            {"name": "exact", "stdin": "4\n1\n2\n3\n4\n2\n",    "expected": "1 2\n3 4"},
            {"name": "k1",    "stdin": "3\n1\n2\n3\n1\n",       "expected": "1\n2\n3", "hidden": True},
        ],
    },
    {
        "slug": "py-prefix-sums",
        "title": "Prefix sums",
        "prompt": "Read N then N integers. Print the prefix sums (inclusive, starting from index 0), space-separated.",
        "starter": "n = int(input())\nnumbers = [int(input()) for _ in range(n)]\n",
        "ref": (
            "n=int(input());xs=[int(input()) for _ in range(n)]\n"
            "out=[];s=0\nfor x in xs:s+=x;out.append(s)\nprint(*out)\n"
        ),
        "cases": [
            {"name": "basic", "stdin": "4\n1\n2\n3\n4\n", "expected": "1 3 6 10"},
            {"name": "neg",   "stdin": "3\n-1\n2\n-3\n",  "expected": "-1 1 -2"},
            {"name": "one",   "stdin": "1\n5\n",           "expected": "5", "hidden": True},
        ],
    },
    {
        "slug": "py-diagonal-sum",
        "title": "Matrix diagonal sum",
        "prompt": "Read N then N rows of N integers. Print the sum of the main diagonal.",
        "starter": "n = int(input())\nmatrix = [list(map(int, input().split())) for _ in range(n)]\n",
        "ref": "n=int(input());m=[list(map(int,input().split())) for _ in range(n)];print(sum(m[i][i] for i in range(n)))\n",
        "cases": [
            {"name": "3x3", "stdin": "3\n1 2 3\n4 5 6\n7 8 9\n", "expected": "15"},
            {"name": "2x2", "stdin": "2\n1 2\n3 4\n",            "expected": "5"},
            {"name": "1x1", "stdin": "1\n7\n",                   "expected": "7", "hidden": True},
        ],
    },
    {
        "slug": "py-reverse-words",
        "title": "Reverse word order",
        "prompt": "Read a line. Print words in reverse order, space-separated.",
        "starter": "sentence = input()\n",
        "ref": "print(*input().split()[::-1])\n",
        "cases": [
            {"name": "basic",  "stdin": "hello world\n",         "expected": "world hello"},
            {"name": "three",  "stdin": "one two three\n",       "expected": "three two one"},
            {"name": "single", "stdin": "word\n",                "expected": "word", "hidden": True},
        ],
    },
    {
        "slug": "py-binary-to-decimal",
        "title": "Binary to decimal",
        "prompt": "Read a binary string (e.g. `1010`). Print its decimal value.",
        "starter": "binary_str = input()\n",
        "ref": "print(int(input(), 2))\n",
        "cases": [
            {"name": "1010",  "stdin": "1010\n",     "expected": "10"},
            {"name": "0",     "stdin": "0\n",        "expected": "0"},
            {"name": "11111111","stdin": "11111111\n","expected": "255", "hidden": True},
        ],
    },
    {
        "slug": "py-longest-common-prefix",
        "title": "Longest common prefix",
        "prompt": "Read N then N strings. Print the longest common prefix of all strings, or empty string if none.",
        "starter": "n = int(input())\nwords = [input() for _ in range(n)]\n",
        "ref": (
            "n=int(input());ws=[input() for _ in range(n)]\n"
            "if not ws:print('');exit()\n"
            "p=ws[0]\n"
            "for w in ws[1:]:\n"
            "    while not w.startswith(p):p=p[:-1]\n"
            "    if not p:break\n"
            "print(p)\n"
        ),
        "cases": [
            {"name": "flower", "stdin": "3\nflower\nflow\nflight\n", "expected": "fl"},
            {"name": "dog",    "stdin": "3\ndog\ncar\nrace\n",       "expected": ""},
            {"name": "same",   "stdin": "2\nabc\nabc\n",             "expected": "abc", "hidden": True},
        ],
    },
    {
        "slug": "py-intersection",
        "title": "List intersection",
        "prompt": "Read M then M integers, then N then N integers. Print sorted intersection (no dupes), one per line.",
        "starter": "m = int(input())\na = [int(input()) for _ in range(m)]\nn = int(input())\nb = [int(input()) for _ in range(n)]\n",
        "ref": (
            "m=int(input());a=set(int(input()) for _ in range(m))\n"
            "n=int(input());b=set(int(input()) for _ in range(n))\n"
            "for x in sorted(a&b):print(x)\n"
        ),
        "cases": [
            {"name": "basic", "stdin": "3\n1\n2\n3\n3\n2\n3\n4\n", "expected": "2\n3"},
            {"name": "none",  "stdin": "2\n1\n2\n2\n3\n4\n",       "expected": ""},
            {"name": "all",   "stdin": "2\n1\n2\n2\n1\n2\n",       "expected": "1\n2", "hidden": True},
        ],
    },
    {
        "slug": "py-matrix-border",
        "title": "Matrix border sum",
        "prompt": "Read N then N rows of N integers. Print the sum of all border elements.",
        "starter": "n = int(input())\nmatrix = [list(map(int, input().split())) for _ in range(n)]\n",
        "ref": (
            "n=int(input());m=[list(map(int,input().split())) for _ in range(n)]\n"
            "s=sum(m[0])+sum(m[-1])+sum(m[i][0] for i in range(1,n-1))+sum(m[i][-1] for i in range(1,n-1))\n"
            "print(s)\n"
        ),
        "cases": [
            {"name": "3x3", "stdin": "3\n1 2 3\n4 5 6\n7 8 9\n", "expected": "40"},
            {"name": "2x2", "stdin": "2\n1 2\n3 4\n",            "expected": "10"},
            {"name": "4x4", "stdin": "4\n1 2 3 4\n5 6 7 8\n9 10 11 12\n13 14 15 16\n","expected": "80", "hidden": True},
        ],
    },
    {
        "slug": "py-number-words",
        "title": "Digit to word",
        "prompt": "Read a single digit 0-9. Print its English word (e.g. `0` → `zero`).",
        "starter": "digit = int(input())\n",
        "ref": (
            'words=["zero","one","two","three","four","five","six","seven","eight","nine"]\n'
            "print(words[int(input())])\n"
        ),
        "cases": [
            {"name": "zero",  "stdin": "0\n", "expected": "zero"},
            {"name": "five",  "stdin": "5\n", "expected": "five"},
            {"name": "nine",  "stdin": "9\n", "expected": "nine", "hidden": True},
        ],
    },
    {
        "slug": "py-flatten-list",
        "title": "Flatten nested list",
        "prompt": "Read N then K1 then K1 ints, K2 then K2 ints, … (N sublists). Print all elements flat, space-separated.",
        "starter": "num_sublists = int(input())\nall_items = []\nfor _ in range(num_sublists):\n    k = int(input())\n    sublist = [input().strip() for _ in range(k)]\n    all_items.append(sublist)\n",
        "ref": (
            "n=int(input());out=[]\n"
            "for _ in range(n):\n"
            "    k=int(input())\n"
            "    for _ in range(k):out.append(input().strip())\n"
            "print(*out)\n"
        ),
        "cases": [
            {"name": "basic", "stdin": "2\n2\n1\n2\n3\n3\n4\n5\n", "expected": "1 2 3 4 5"},
            {"name": "empty", "stdin": "2\n0\n2\n1\n2\n",           "expected": "1 2"},
            {"name": "one",   "stdin": "1\n1\n42\n",                "expected": "42", "hidden": True},
        ],
    },
    {
        "slug": "py-rolling-average",
        "title": "Rolling average",
        "prompt": "Read N then N floats then window size W. Print the rolling average of each window (floor to 2 dp), space-separated.",
        "starter": "n = int(input())\nnumbers = [float(input()) for _ in range(n)]\nw = int(input())\n",
        "ref": (
            "n=int(input());xs=[float(input()) for _ in range(n)];w=int(input())\n"
            'print(" ".join(f"{sum(xs[i:i+w])/w:.2f}" for i in range(n-w+1)))\n'
        ),
        "cases": [
            {"name": "basic",  "stdin": "5\n1\n2\n3\n4\n5\n3\n", "expected": "2.00 3.00 4.00"},
            {"name": "w1",     "stdin": "3\n1\n2\n3\n1\n",       "expected": "1.00 2.00 3.00"},
            {"name": "w-full", "stdin": "4\n1\n2\n3\n4\n4\n",    "expected": "2.50", "hidden": True},
        ],
    },
    {
        "slug": "py-count-vowels-words",
        "title": "Words with most vowels",
        "prompt": "Read N then N words. Print the word(s) with the most vowels (aeiou, case-insensitive). If tie, print all in input order, one per line.",
        "starter": "n = int(input())\nwords = [input() for _ in range(n)]\n",
        "ref": (
            "n=int(input());ws=[input() for _ in range(n)]\n"
            "vc=lambda w:sum(1 for c in w.lower() if c in 'aeiou')\n"
            "mx=max(vc(w) for w in ws)\n"
            "for w in ws:\n"
            "    if vc(w)==mx:print(w)\n"
        ),
        "cases": [
            {"name": "basic", "stdin": "3\nhello\nworld\naeiou\n", "expected": "aeiou"},
            {"name": "tie",   "stdin": "2\naeio\nbcdu\n",          "expected": "aeio"},
            {"name": "one",   "stdin": "1\ncat\n",                 "expected": "cat", "hidden": True},
        ],
    },
    {
        "slug": "py-collatz",
        "title": "Collatz sequence",
        "prompt": "Read N. Print the Collatz sequence starting at N until reaching 1, one number per line (including N and 1).",
        "starter": "n = int(input())\n",
        "ref": (
            "n=int(input())\n"
            "while True:\n"
            "    print(n)\n"
            "    if n==1:break\n"
            "    n=n//2 if n%2==0 else 3*n+1\n"
        ),
        "cases": [
            {"name": "6",  "stdin": "6\n",  "expected": "6\n3\n10\n5\n16\n8\n4\n2\n1"},
            {"name": "1",  "stdin": "1\n",  "expected": "1"},
            {"name": "4",  "stdin": "4\n",  "expected": "4\n2\n1", "hidden": True},
        ],
    },
    {
        "slug": "py-valid-ip",
        "title": "Valid IPv4",
        "prompt": "Read a string. Print `yes` if valid IPv4 (four octets 0-255 dot-separated, no leading zeros), else `no`.",
        "starter": "s = input()\n",
        "ref": (
            "s=input().split('.')\n"
            "def ok(p):\n"
            "    if not p.isdigit():return False\n"
            "    if len(p)>1 and p[0]=='0':return False\n"
            "    return 0<=int(p)<=255\n"
            'print("yes" if len(s)==4 and all(ok(p) for p in s) else "no")\n'
        ),
        "cases": [
            {"name": "valid",   "stdin": "192.168.1.1\n",  "expected": "yes"},
            {"name": "invalid", "stdin": "256.0.0.1\n",    "expected": "no"},
            {"name": "leading", "stdin": "01.02.03.04\n",  "expected": "no", "hidden": True},
        ],
    },
]

PY_HARD_2 = [
    {
        "slug": "py-lcs-length",
        "title": "Longest common subsequence",
        "prompt": "Read two strings S and T. Print the length of their longest common subsequence.",
        "starter": "s = input()\nt = input()\n",
        "ref": (
            "s=input();t=input()\n"
            "m,n=len(s),len(t)\n"
            "dp=[[0]*(n+1) for _ in range(m+1)]\n"
            "for i in range(1,m+1):\n"
            "    for j in range(1,n+1):\n"
            "        dp[i][j]=dp[i-1][j-1]+1 if s[i-1]==t[j-1] else max(dp[i-1][j],dp[i][j-1])\n"
            "print(dp[m][n])\n"
        ),
        "cases": [
            {"name": "abcde-ace",  "stdin": "abcde\nace\n",   "expected": "3"},
            {"name": "abc-abc",    "stdin": "abc\nabc\n",     "expected": "3"},
            {"name": "abc-def",    "stdin": "abc\ndef\n",     "expected": "0", "hidden": True},
            {"name": "long",       "stdin": "AGGTAB\nGXTXAYB\n","expected": "4", "hidden": True},
        ],
    },
    {
        "slug": "py-edit-distance",
        "title": "Edit distance",
        "prompt": "Read two strings. Print the minimum edit distance (insert/delete/replace each cost 1).",
        "starter": "s = input()\nt = input()\n",
        "ref": (
            "s=input();t=input()\n"
            "m,n=len(s),len(t)\n"
            "dp=[[0]*(n+1) for _ in range(m+1)]\n"
            "for i in range(m+1):dp[i][0]=i\n"
            "for j in range(n+1):dp[0][j]=j\n"
            "for i in range(1,m+1):\n"
            "    for j in range(1,n+1):\n"
            "        dp[i][j]=dp[i-1][j-1] if s[i-1]==t[j-1] else 1+min(dp[i-1][j],dp[i][j-1],dp[i-1][j-1])\n"
            "print(dp[m][n])\n"
        ),
        "cases": [
            {"name": "horse-ros",  "stdin": "horse\nros\n",    "expected": "3"},
            {"name": "intention-execution", "stdin": "intention\nexecution\n", "expected": "5"},
            {"name": "same",       "stdin": "abc\nabc\n",      "expected": "0", "hidden": True},
        ],
    },
    {
        "slug": "py-knapsack-01",
        "title": "0/1 Knapsack",
        "prompt": "Read N (items) then W (capacity), then N pairs `value weight`. Print max value fitting in capacity.",
        "starter": "n = int(input())\nW = int(input())\nitems = [tuple(map(int, input().split())) for _ in range(n)]  # each item: (value, weight)\n",
        "ref": (
            "n=int(input());w=int(input())\n"
            "items=[tuple(map(int,input().split())) for _ in range(n)]\n"
            "dp=[0]*(w+1)\n"
            "for v,wt in items:\n"
            "    for j in range(w,wt-1,-1):\n"
            "        dp[j]=max(dp[j],dp[j-wt]+v)\n"
            "print(dp[w])\n"
        ),
        "cases": [
            {"name": "basic",  "stdin": "3\n50\n60 10\n100 20\n120 30\n", "expected": "220"},
            {"name": "empty",  "stdin": "2\n2\n4 3\n5 4\n",              "expected": "0"},
            {"name": "exact",  "stdin": "2\n10\n6 5\n9 5\n",             "expected": "15", "hidden": True},
        ],
    },
    {
        "slug": "py-max-subarray-product",
        "title": "Maximum subarray product",
        "prompt": "Read N then N integers. Print the maximum product of a contiguous subarray.",
        "starter": "n = int(input())\nnumbers = [int(input()) for _ in range(n)]\n",
        "ref": (
            "n=int(input());xs=[int(input()) for _ in range(n)]\n"
            "mx=mn=best=xs[0]\n"
            "for x in xs[1:]:\n"
            "    mx,mn=max(x,mx*x,mn*x),min(x,mx*x,mn*x)\n"
            "    best=max(best,mx)\n"
            "print(best)\n"
        ),
        "cases": [
            {"name": "basic",    "stdin": "6\n2\n3\n-2\n4\n-1\n3\n", "expected": "24"},
            {"name": "all-neg",  "stdin": "3\n-2\n-3\n-1\n",         "expected": "6"},
            {"name": "single",   "stdin": "1\n-5\n",                  "expected": "-5", "hidden": True},
        ],
    },
    {
        "slug": "py-jump-game",
        "title": "Jump game",
        "prompt": "Read N then N non-negative integers (max jump from each index). Print `yes` if you can reach the last index from index 0, else `no`.",
        "starter": "n = int(input())\njumps = [int(input()) for _ in range(n)]\n",
        "ref": (
            "n=int(input());xs=[int(input()) for _ in range(n)]\n"
            "reach=0\n"
            "for i,x in enumerate(xs):\n"
            "    if i>reach:break\n"
            "    reach=max(reach,i+x)\n"
            'print("yes" if reach>=n-1 else "no")\n'
        ),
        "cases": [
            {"name": "yes", "stdin": "5\n2\n3\n1\n1\n4\n", "expected": "yes"},
            {"name": "no",  "stdin": "5\n3\n2\n1\n0\n4\n", "expected": "no"},
            {"name": "one", "stdin": "1\n0\n",              "expected": "yes", "hidden": True},
        ],
    },
    {
        "slug": "py-subset-sum",
        "title": "Subset sum",
        "prompt": "Read N then N integers then target T. Print `yes` if any subset sums to T, else `no`.",
        "starter": "n = int(input())\nnumbers = [int(input()) for _ in range(n)]\ntarget = int(input())\n",
        "ref": (
            "n=int(input());xs=[int(input()) for _ in range(n)];t=int(input())\n"
            "dp={0}\n"
            "for x in xs:dp|={s+x for s in dp}\n"
            'print("yes" if t in dp else "no")\n'
        ),
        "cases": [
            {"name": "yes",  "stdin": "4\n1\n5\n11\n5\n11\n", "expected": "yes"},
            {"name": "no",   "stdin": "3\n1\n2\n5\n4\n",      "expected": "no"},
            {"name": "zero", "stdin": "2\n3\n4\n0\n",          "expected": "yes", "hidden": True},
        ],
    },
    {
        "slug": "py-lis-length",
        "title": "Longest increasing subsequence",
        "prompt": "Read N then N integers. Print the length of the longest strictly increasing subsequence.",
        "starter": "n = int(input())\nnumbers = [int(input()) for _ in range(n)]\n",
        "ref": (
            "import bisect\n"
            "n=int(input());xs=[int(input()) for _ in range(n)]\n"
            "tails=[]\n"
            "for x in xs:\n"
            "    i=bisect.bisect_left(tails,x)\n"
            "    if i==len(tails):tails.append(x)\n"
            "    else:tails[i]=x\n"
            "print(len(tails))\n"
        ),
        "cases": [
            {"name": "basic",  "stdin": "8\n10\n9\n2\n5\n3\n7\n101\n18\n", "expected": "4"},
            {"name": "sorted", "stdin": "4\n1\n2\n3\n4\n",                  "expected": "4"},
            {"name": "desc",   "stdin": "4\n4\n3\n2\n1\n",                  "expected": "1", "hidden": True},
        ],
    },
    {
        "slug": "py-trapping-rain",
        "title": "Trapping rain water",
        "prompt": "Read N then N non-negative integers (heights). Print total trapped water units.",
        "starter": "n = int(input())\nheights = [int(input()) for _ in range(n)]\n",
        "ref": (
            "n=int(input());h=[int(input()) for _ in range(n)]\n"
            "if n<3:print(0);exit()\n"
            "l,r=0,n-1;lm=rm=0;ans=0\n"
            "while l<r:\n"
            "    if h[l]<h[r]:\n"
            "        lm=max(lm,h[l]);ans+=lm-h[l];l+=1\n"
            "    else:\n"
            "        rm=max(rm,h[r]);ans+=rm-h[r];r-=1\n"
            "print(ans)\n"
        ),
        "cases": [
            {"name": "basic",  "stdin": "12\n0\n1\n0\n2\n1\n0\n1\n3\n2\n1\n2\n1\n", "expected": "6"},
            {"name": "flat",   "stdin": "3\n3\n3\n3\n",                              "expected": "0"},
            {"name": "valley", "stdin": "3\n2\n0\n2\n",                              "expected": "2", "hidden": True},
        ],
    },
    {
        "slug": "py-house-robber",
        "title": "House robber",
        "prompt": "Read N then N non-negative integers (loot per house). No two adjacent. Print max loot.",
        "starter": "n = int(input())\nloot = [int(input()) for _ in range(n)]\n",
        "ref": (
            "n=int(input());xs=[int(input()) for _ in range(n)]\n"
            "a=b=0\n"
            "for x in xs:a,b=b,max(b,a+x)\n"
            "print(b)\n"
        ),
        "cases": [
            {"name": "basic",  "stdin": "4\n1\n2\n3\n1\n", "expected": "4"},
            {"name": "bigger", "stdin": "4\n2\n7\n9\n3\n", "expected": "12"},
            {"name": "one",    "stdin": "1\n5\n",           "expected": "5", "hidden": True},
        ],
    },
    {
        "slug": "py-decode-ways",
        "title": "Decode ways",
        "prompt": "A string of digits maps to letters (1→A, 2→B … 26→Z). Read a digit string. Print the number of ways to decode it. 0 if impossible.",
        "starter": "s = input()\n",
        "ref": (
            "s=input()\n"
            "n=len(s)\n"
            "if not s or s[0]=='0':print(0);exit()\n"
            "dp=[0]*(n+1);dp[0]=dp[1]=1\n"
            "for i in range(2,n+1):\n"
            "    if s[i-1]!='0':dp[i]+=dp[i-1]\n"
            "    two=int(s[i-2:i])\n"
            "    if 10<=two<=26:dp[i]+=dp[i-2]\n"
            "print(dp[n])\n"
        ),
        "cases": [
            {"name": "12",   "stdin": "12\n",   "expected": "2"},
            {"name": "226",  "stdin": "226\n",  "expected": "3"},
            {"name": "0",    "stdin": "0\n",    "expected": "0", "hidden": True},
            {"name": "10",   "stdin": "10\n",   "expected": "1", "hidden": True},
        ],
    },
    {
        "slug": "py-sliding-window-max",
        "title": "Sliding window maximum",
        "prompt": "Read N then N integers then window size K. Print max of each window, space-separated.",
        "starter": "n = int(input())\nnumbers = [int(input()) for _ in range(n)]\nk = int(input())\n",
        "ref": (
            "from collections import deque\n"
            "n=int(input());xs=[int(input()) for _ in range(n)];k=int(input())\n"
            "dq=deque();out=[]\n"
            "for i,x in enumerate(xs):\n"
            "    while dq and xs[dq[-1]]<=x:dq.pop()\n"
            "    dq.append(i)\n"
            "    if dq[0]<=i-k:dq.popleft()\n"
            "    if i>=k-1:out.append(xs[dq[0]])\n"
            "print(*out)\n"
        ),
        "cases": [
            {"name": "basic",  "stdin": "8\n1\n3\n-1\n-3\n5\n3\n6\n7\n3\n", "expected": "3 3 5 5 6 7"},
            {"name": "k1",     "stdin": "4\n1\n2\n3\n4\n1\n",               "expected": "1 2 3 4"},
            {"name": "all-same","stdin": "4\n5\n5\n5\n5\n2\n",              "expected": "5 5 5", "hidden": True},
        ],
    },
    {
        "slug": "py-word-break",
        "title": "Word break",
        "prompt": "Read S then N then N dictionary words. Print `yes` if S can be segmented into dictionary words, else `no`.",
        "starter": "s = input()\nn = int(input())\nwords = [input() for _ in range(n)]\n",
        "ref": (
            "s=input();n=int(input());words=set(input() for _ in range(n))\n"
            "ln=len(s);dp=[False]*(ln+1);dp[0]=True\n"
            "for i in range(1,ln+1):\n"
            "    for w in words:\n"
            "        lw=len(w)\n"
            "        if i>=lw and dp[i-lw] and s[i-lw:i]==w:dp[i]=True;break\n"
            'print("yes" if dp[ln] else "no")\n'
        ),
        "cases": [
            {"name": "yes",  "stdin": "leetcode\n2\nleet\ncode\n",        "expected": "yes"},
            {"name": "no",   "stdin": "catsandog\n3\ncats\ndog\nsand\n",  "expected": "no"},
            {"name": "one",  "stdin": "hello\n1\nhello\n",                "expected": "yes", "hidden": True},
        ],
    },
    {
        "slug": "py-matrix-spiral",
        "title": "Spiral order matrix",
        "prompt": "Read N then N rows of N integers. Print all elements in spiral order (clockwise), space-separated.",
        "starter": "n = int(input())\nmatrix = [list(map(int, input().split())) for _ in range(n)]\n",
        "ref": (
            "n=int(input());m=[list(map(int,input().split())) for _ in range(n)]\n"
            "out=[]\n"
            "while m:\n"
            "    out+=m.pop(0)\n"
            "    m=[list(r) for r in zip(*m)][::-1]\n"
            "print(*out)\n"
        ),
        "cases": [
            {"name": "3x3", "stdin": "3\n1 2 3\n4 5 6\n7 8 9\n", "expected": "1 2 3 6 9 8 7 4 5"},
            {"name": "1x1", "stdin": "1\n1\n",                   "expected": "1"},
            {"name": "2x2", "stdin": "2\n1 2\n3 4\n",            "expected": "1 2 4 3", "hidden": True},
        ],
    },
    {
        "slug": "py-valid-sudoku-row",
        "title": "Valid sudoku row",
        "prompt": "Read 9 integers (1-9 or 0 for empty). Print `yes` if no digit 1-9 appears twice (zeros ignored), else `no`.",
        "starter": "row = [int(input()) for _ in range(9)]\n",
        "ref": (
            "xs=[int(input()) for _ in range(9)]\n"
            "filled=[x for x in xs if x!=0]\n"
            'print("yes" if len(filled)==len(set(filled)) else "no")\n'
        ),
        "cases": [
            {"name": "valid",   "stdin": "5\n3\n0\n0\n7\n0\n0\n0\n0\n", "expected": "yes"},
            {"name": "invalid", "stdin": "5\n3\n5\n0\n7\n0\n0\n0\n0\n", "expected": "no"},
            {"name": "all-zero","stdin": "0\n0\n0\n0\n0\n0\n0\n0\n0\n", "expected": "yes", "hidden": True},
        ],
    },
    {
        "slug": "py-zigzag-string",
        "title": "Zigzag conversion",
        "prompt": "Read string S and number of rows R. Print the zigzag reading (top to bottom, left to right by row).",
        "starter": "s = input()\nr = int(input())\n",
        "ref": (
            "s=input();r=int(input())\n"
            "if r==1 or r>=len(s):print(s);exit()\n"
            "rows=['' for _ in range(r)];cur=0;down=True\n"
            "for c in s:\n"
            "    rows[cur]+=c\n"
            "    if cur==0:down=True\n"
            "    elif cur==r-1:down=False\n"
            "    cur+=1 if down else -1\n"
            'print("".join(rows))\n'
        ),
        "cases": [
            {"name": "basic", "stdin": "PAYPALISHIRING\n3\n", "expected": "PAHNAPLSIIGYIR"},
            {"name": "4rows", "stdin": "PAYPALISHIRING\n4\n", "expected": "PINALSIGYAHRPI"},
            {"name": "r1",    "stdin": "ABC\n1\n",            "expected": "ABC", "hidden": True},
        ],
    },
    {
        "slug": "py-count-paths",
        "title": "Count paths in grid (obstacles)",
        "prompt": "Read M and N then M rows of N space-separated values (0=open, 1=blocked). Count paths top-left to bottom-right (right/down only).",
        "starter": "m = int(input())\nn = int(input())\ngrid = [list(map(int, input().split())) for _ in range(m)]\n",
        "ref": (
            "m=int(input());n=int(input())\n"
            "g=[list(map(int,input().split())) for _ in range(m)]\n"
            "if g[0][0] or g[m-1][n-1]:print(0);exit()\n"
            "dp=[[0]*n for _ in range(m)];dp[0][0]=1\n"
            "for i in range(m):\n"
            "    for j in range(n):\n"
            "        if g[i][j]:dp[i][j]=0\n"
            "        else:\n"
            "            if i:dp[i][j]+=dp[i-1][j]\n"
            "            if j:dp[i][j]+=dp[i][j-1]\n"
            "print(dp[m-1][n-1])\n"
        ),
        "cases": [
            {"name": "clear",    "stdin": "3\n3\n0 0 0\n0 0 0\n0 0 0\n", "expected": "6"},
            {"name": "blocked",  "stdin": "3\n3\n0 0 0\n0 1 0\n0 0 0\n", "expected": "2"},
            {"name": "no-path",  "stdin": "2\n2\n0 1\n1 0\n",            "expected": "0", "hidden": True},
        ],
    },
    {
        "slug": "py-string-permutations",
        "title": "Count string permutations",
        "prompt": "Read a string. Print the number of distinct permutations.",
        "starter": "s = input()\n",
        "ref": (
            "from math import factorial\nfrom collections import Counter\n"
            "s=input();c=Counter(s)\n"
            "n=factorial(len(s))\n"
            "for v in c.values():n//=factorial(v)\n"
            "print(n)\n"
        ),
        "cases": [
            {"name": "abc",   "stdin": "abc\n",   "expected": "6"},
            {"name": "aab",   "stdin": "aab\n",   "expected": "3"},
            {"name": "aaaa",  "stdin": "aaaa\n",  "expected": "1", "hidden": True},
        ],
    },
    {
        "slug": "py-matrix-multiplication",
        "title": "Matrix multiplication",
        "prompt": "Read N then N rows of N ints (matrix A), then N rows of N ints (matrix B). Print A×B (rows space-separated).",
        "starter": "n = int(input())\nA = [list(map(int, input().split())) for _ in range(n)]\nB = [list(map(int, input().split())) for _ in range(n)]\n",
        "ref": (
            "n=int(input())\n"
            "A=[list(map(int,input().split())) for _ in range(n)]\n"
            "B=[list(map(int,input().split())) for _ in range(n)]\n"
            "C=[[sum(A[i][k]*B[k][j] for k in range(n)) for j in range(n)] for i in range(n)]\n"
            'print("\\n".join(" ".join(map(str,r)) for r in C))\n'
        ),
        "cases": [
            {"name": "2x2", "stdin": "2\n1 2\n3 4\n5 6\n7 8\n", "expected": "19 22\n43 50"},
            {"name": "1x1", "stdin": "1\n3\n4\n",               "expected": "12"},
            {"name": "identity", "stdin": "2\n1 0\n0 1\n2 3\n4 5\n","expected": "2 3\n4 5", "hidden": True},
        ],
    },
    {
        "slug": "py-count-inversions",
        "title": "Count inversions",
        "prompt": "Read N then N integers. Print the number of inversions (pairs i<j where a[i]>a[j]).",
        "starter": "n = int(input())\nnumbers = [int(input()) for _ in range(n)]\n",
        "ref": (
            "def merge_count(arr):\n"
            "    if len(arr)<2:return arr,0\n"
            "    m=len(arr)//2\n"
            "    l,lc=merge_count(arr[:m]);r,rc=merge_count(arr[m:])\n"
            "    merged=[];inv=lc+rc;i=j=0\n"
            "    while i<len(l) and j<len(r):\n"
            "        if l[i]<=r[j]:merged.append(l[i]);i+=1\n"
            "        else:merged.append(r[j]);inv+=len(l)-i;j+=1\n"
            "    merged+=l[i:]+r[j:];return merged,inv\n"
            "n=int(input());xs=[int(input()) for _ in range(n)]\n"
            "_,c=merge_count(xs);print(c)\n"
        ),
        "cases": [
            {"name": "basic",  "stdin": "6\n2\n4\n1\n3\n5\n6\n", "expected": "3"},
            {"name": "sorted", "stdin": "4\n1\n2\n3\n4\n",        "expected": "0"},
            {"name": "rev",    "stdin": "4\n4\n3\n2\n1\n",        "expected": "6", "hidden": True},
        ],
    },
    {
        "slug": "py-graph-bfs",
        "title": "BFS shortest path",
        "prompt": "Read N (nodes 0..N-1), M edges, M pairs `u v`, then S and T. Print shortest path length from S to T, or `-1`.",
        "starter": "n = int(input())\nm = int(input())\nedges = [tuple(map(int, input().split())) for _ in range(m)]\nstart = int(input())\nend = int(input())\n",
        "ref": (
            "from collections import deque\n"
            "n=int(input());m=int(input());g=[[] for _ in range(n)]\n"
            "for _ in range(m):u,v=map(int,input().split());g[u].append(v);g[v].append(u)\n"
            "s,t=int(input()),int(input())\n"
            "dist=[-1]*n;dist[s]=0;q=deque([s])\n"
            "while q:\n"
            "    u=q.popleft()\n"
            "    for v in g[u]:\n"
            "        if dist[v]==-1:dist[v]=dist[u]+1;q.append(v)\n"
            "print(dist[t])\n"
        ),
        "cases": [
            {"name": "direct",   "stdin": "4\n4\n0 1\n1 2\n2 3\n0 3\n0\n3\n", "expected": "1"},
            {"name": "longer",   "stdin": "4\n3\n0 1\n1 2\n2 3\n0\n3\n",      "expected": "3"},
            {"name": "unreachable","stdin": "4\n2\n0 1\n2 3\n0\n3\n",         "expected": "-1", "hidden": True},
        ],
    },
    {
        "slug": "py-regex-wildcard",
        "title": "Wildcard match",
        "prompt": "Read pattern P (with `?` = any char, `*` = zero or more chars) then string S. Print `yes` if full match, else `no`.",
        "starter": "pattern = input()\ns = input()\n",
        "ref": (
            "p=input();s=input()\n"
            "m,n=len(p),len(s)\n"
            "dp=[[False]*(n+1) for _ in range(m+1)];dp[0][0]=True\n"
            "for i in range(1,m+1):\n"
            "    if p[i-1]=='*':dp[i][0]=dp[i-1][0]\n"
            "for i in range(1,m+1):\n"
            "    for j in range(1,n+1):\n"
            "        if p[i-1]=='*':dp[i][j]=dp[i-1][j] or dp[i][j-1]\n"
            "        elif p[i-1]=='?' or p[i-1]==s[j-1]:dp[i][j]=dp[i-1][j-1]\n"
            'print("yes" if dp[m][n] else "no")\n'
        ),
        "cases": [
            {"name": "star",   "stdin": "a*b\naXXb\n", "expected": "yes"},
            {"name": "qmark",  "stdin": "a?c\nabc\n",  "expected": "yes"},
            {"name": "no",     "stdin": "abc\nab\n",   "expected": "no", "hidden": True},
            {"name": "all-star","stdin": "*\n\n",       "expected": "yes", "hidden": True},
        ],
    },
    {
        "slug": "py-minimum-coins-change",
        "title": "Coin change (ways)",
        "prompt": "Read M coin denominations then target T. Print total number of ways to make T using unlimited coins.",
        "starter": "m = int(input())\ncoins = [int(input()) for _ in range(m)]\ntarget = int(input())\n",
        "ref": (
            "m=int(input());coins=[int(input()) for _ in range(m)];t=int(input())\n"
            "dp=[0]*(t+1);dp[0]=1\n"
            "for c in coins:\n"
            "    for i in range(c,t+1):dp[i]+=dp[i-c]\n"
            "print(dp[t])\n"
        ),
        "cases": [
            {"name": "basic",  "stdin": "3\n1\n2\n5\n5\n", "expected": "4"},
            {"name": "no-way", "stdin": "2\n2\n4\n3\n",    "expected": "0"},
            {"name": "one-way","stdin": "1\n1\n4\n",        "expected": "1", "hidden": True},
        ],
    },
]


WEB_EASY_2 = [
    {
        "slug": "web-heading-hierarchy",
        "title": "Heading hierarchy",
        "prompt": "Render an `<h1>`, `<h2>`, and `<h3>` with any text.",
        "starter": "",
        "ref": "<h1>a</h1><h2>b</h2><h3>c</h3>",
        "cases": [
            {"name": "has all", "assertions": [
                {"kind": "selector", "selector": "h1"},
                {"kind": "selector", "selector": "h2"},
                {"kind": "selector", "selector": "h3"},
            ]},
        ],
    },
    {
        "slug": "web-ordered-list",
        "title": "Ordered list",
        "prompt": "Render an `<ol>` with exactly 4 `<li>` items.",
        "starter": "",
        "ref": "<ol><li>a</li><li>b</li><li>c</li><li>d</li></ol>",
        "cases": [
            {"name": "four items", "assertions": [
                {"kind": "count", "selector": "ol li", "count": 4},
            ]},
        ],
    },
    {
        "slug": "web-table-basic",
        "title": "Table rows",
        "prompt": "Render a `<table>` with exactly 3 `<tr>` rows, each containing 2 `<td>` cells.",
        "starter": "",
        "ref": "<table><tr><td>a</td><td>b</td></tr><tr><td>c</td><td>d</td></tr><tr><td>e</td><td>f</td></tr></table>",
        "cases": [
            {"name": "3 rows",    "assertions": [{"kind": "count", "selector": "table tr",    "count": 3}]},
            {"name": "6 cells",   "assertions": [{"kind": "count", "selector": "table td",    "count": 6}]},
        ],
    },
    {
        "slug": "web-checkbox-input",
        "title": "Checkbox with label",
        "prompt": "Render a `<label>` containing an `<input type=\"checkbox\" id=\"agree\">` and the text **I agree**.",
        "starter": "",
        "ref": "<label><input type='checkbox' id='agree'> I agree</label>",
        "cases": [
            {"name": "checkbox", "assertions": [
                {"kind": "selector", "selector": "input[type=checkbox][id=agree]"},
                {"kind": "selector", "selector": "label"},
            ]},
        ],
    },
    {
        "slug": "web-radio-group",
        "title": "Radio button group",
        "prompt": "Render two `<input type=\"radio\" name=\"choice\">` buttons with values `yes` and `no`.",
        "starter": "",
        "ref": "<input type='radio' name='choice' value='yes'><input type='radio' name='choice' value='no'>",
        "cases": [
            {"name": "two radios", "assertions": [
                {"kind": "count", "selector": "input[type=radio][name=choice]", "count": 2},
                {"kind": "selector", "selector": "input[value=yes]"},
                {"kind": "selector", "selector": "input[value=no]"},
            ]},
        ],
    },
    {
        "slug": "web-textarea-placeholder",
        "title": "Textarea with placeholder",
        "prompt": "Render a `<textarea placeholder=\"Write here…\">` with `id=\"msg\"`.",
        "starter": "",
        "ref": "<textarea id='msg' placeholder='Write here…'></textarea>",
        "cases": [
            {"name": "placeholder", "assertions": [
                {"kind": "attr", "selector": "textarea#msg", "attr": "placeholder", "value": "Write here…"},
            ]},
        ],
    },
    {
        "slug": "web-select-options",
        "title": "Select dropdown",
        "prompt": "Render a `<select id=\"lang\">` with three `<option>` values: `py`, `js`, `go`.",
        "starter": "",
        "ref": "<select id='lang'><option value='py'>py</option><option value='js'>js</option><option value='go'>go</option></select>",
        "cases": [
            {"name": "three options", "assertions": [
                {"kind": "count", "selector": "#lang option", "count": 3},
            ]},
        ],
    },
    {
        "slug": "web-data-attribute",
        "title": "Data attribute",
        "prompt": "Add `data-role=\"admin\"` to a `<div id=\"user\">`.",
        "starter": "<div id='user'></div>",
        "ref": "<div id='user' data-role='admin'></div>",
        "cases": [
            {"name": "data-role", "assertions": [
                {"kind": "attr", "selector": "#user", "attr": "data-role", "value": "admin"},
            ]},
        ],
    },
    {
        "slug": "web-progress-element",
        "title": "Progress element",
        "prompt": "Render `<progress id=\"p\" max=\"100\" value=\"50\"></progress>`.",
        "starter": "",
        "ref": "<progress id='p' max='100' value='50'></progress>",
        "cases": [
            {"name": "value", "assertions": [
                {"kind": "js", "expr": "document.querySelector('#p').value === 50"},
            ]},
        ],
    },
    {
        "slug": "web-center-text",
        "title": "Centre text",
        "prompt": "Make `.centered` have `text-align: center`.",
        "starter": "<p class='centered'>hello</p>\n<style>\n</style>",
        "ref": "<style>.centered{text-align:center}</style><p class='centered'>hello</p>",
        "cases": [
            {"name": "centered", "assertions": [
                {"kind": "js", "expr": "getComputedStyle(document.querySelector('.centered')).textAlign === 'center'"},
            ]},
        ],
    },
    {
        "slug": "web-border-style",
        "title": "Bordered box",
        "prompt": "Give `.box` a 2px solid black border.",
        "starter": "<div class='box'>hi</div>\n<style>\n</style>",
        "ref": "<style>.box{border:2px solid black}</style><div class='box'>hi</div>",
        "cases": [
            {"name": "border", "assertions": [
                {"kind": "js", "expr": "getComputedStyle(document.querySelector('.box')).borderTopStyle === 'solid'"},
                {"kind": "js", "expr": "parseFloat(getComputedStyle(document.querySelector('.box')).borderTopWidth) === 2"},
            ]},
        ],
    },
    {
        "slug": "web-font-size-20",
        "title": "Font size 20px",
        "prompt": "Set `font-size: 20px` on `.big`.",
        "starter": "<p class='big'>text</p>\n<style>\n</style>",
        "ref": "<style>.big{font-size:20px}</style><p class='big'>text</p>",
        "cases": [
            {"name": "20px", "assertions": [
                {"kind": "js", "expr": "parseFloat(getComputedStyle(document.querySelector('.big')).fontSize) === 20"},
            ]},
        ],
    },
    {
        "slug": "web-hidden-element",
        "title": "Hide an element",
        "prompt": "Set `display: none` on `#secret`.",
        "starter": "<div id='secret'>hidden</div>\n<style>\n</style>",
        "ref": "<style>#secret{display:none}</style><div id='secret'>hidden</div>",
        "cases": [
            {"name": "hidden", "assertions": [
                {"kind": "js", "expr": "getComputedStyle(document.querySelector('#secret')).display === 'none'"},
            ]},
        ],
    },
    {
        "slug": "web-opacity-half",
        "title": "Half opacity",
        "prompt": "Set `opacity: 0.5` on `.faded`.",
        "starter": "<div class='faded'>text</div>\n<style>\n</style>",
        "ref": "<style>.faded{opacity:0.5}</style><div class='faded'>text</div>",
        "cases": [
            {"name": "opacity", "assertions": [
                {"kind": "js", "expr": "parseFloat(getComputedStyle(document.querySelector('.faded')).opacity) === 0.5"},
            ]},
        ],
    },
    {
        "slug": "web-css-variable",
        "title": "CSS custom property",
        "prompt": "Define `--brand: #ff0000` on `:root`. Apply it as the `color` of `.logo`.",
        "starter": "<p class='logo'>Brand</p>\n<style>\n</style>",
        "ref": "<style>:root{--brand:#ff0000}.logo{color:var(--brand)}</style><p class='logo'>Brand</p>",
        "cases": [
            {"name": "brand color", "assertions": [
                {"kind": "js", "expr": "getComputedStyle(document.querySelector('.logo')).color === 'rgb(255, 0, 0)'"},
            ]},
        ],
    },
    {
        "slug": "web-hover-underline",
        "title": "Underline on hover",
        "prompt": "`.link` should have `text-decoration: underline` on hover. Add the CSS rule.",
        "starter": "<a class='link'>click</a>\n<style>\n</style>",
        "ref": "<style>.link:hover{text-decoration:underline}</style><a class='link'>click</a>",
        "cases": [
            {"name": "rule exists", "assertions": [
                {"kind": "js", "expr": "Array.from(document.styleSheets).some(ss=>{try{return Array.from(ss.cssRules).some(r=>r.selectorText&&r.selectorText.includes('.link:hover'))}catch{return false}})"},
            ]},
        ],
    },
    {
        "slug": "web-list-no-bullets",
        "title": "List without bullets",
        "prompt": "Remove default bullets from `ul.plain` (set `list-style: none`).",
        "starter": "<ul class='plain'><li>a</li><li>b</li></ul>\n<style>\n</style>",
        "ref": "<style>ul.plain{list-style:none}</style><ul class='plain'><li>a</li><li>b</li></ul>",
        "cases": [
            {"name": "no bullets", "assertions": [
                {"kind": "js", "expr": "getComputedStyle(document.querySelector('ul.plain')).listStyleType === 'none'"},
            ]},
        ],
    },
    {
        "slug": "web-text-uppercase-css",
        "title": "Uppercase text via CSS",
        "prompt": "Apply `text-transform: uppercase` to `.shout`.",
        "starter": "<p class='shout'>hello</p>\n<style>\n</style>",
        "ref": "<style>.shout{text-transform:uppercase}</style><p class='shout'>hello</p>",
        "cases": [
            {"name": "uppercase", "assertions": [
                {"kind": "js", "expr": "getComputedStyle(document.querySelector('.shout')).textTransform === 'uppercase'"},
            ]},
        ],
    },
    {
        "slug": "web-transition-bg",
        "title": "Background colour transition",
        "prompt": "Give `.btn` `background: blue` and a `transition: background 0.3s` so hover changes to red.",
        "starter": "<button class='btn'>click</button>\n<style>\n</style>",
        "ref": "<style>.btn{background:blue;transition:background 0.3s}.btn:hover{background:red}</style><button class='btn'>click</button>",
        "cases": [
            {"name": "transition set", "assertions": [
                {"kind": "js", "expr": "getComputedStyle(document.querySelector('.btn')).transitionProperty.includes('background')"},
            ]},
        ],
    },
    {
        "slug": "web-set-style-js",
        "title": "Set style via JS",
        "prompt": "Write JS that sets `#box`'s background colour to `lime` on page load.",
        "starter": "<div id='box'>hi</div>\n<script>\n</script>",
        "ref": "<div id='box'>hi</div><script>document.getElementById('box').style.background='lime'</script>",
        "cases": [
            {"name": "lime bg", "assertions": [
                {"kind": "js", "expr": "getComputedStyle(document.querySelector('#box')).backgroundColor === 'rgb(0, 255, 0)'"},
            ]},
        ],
    },
    {
        "slug": "web-count-elements",
        "title": "Count elements via JS",
        "prompt": "Write JS that sets `window.count` to the number of `<li>` elements in the page.",
        "starter": "<ul><li>a</li><li>b</li><li>c</li></ul>\n<script>\n</script>",
        "ref": "<ul><li>a</li><li>b</li><li>c</li></ul><script>window.count=document.querySelectorAll('li').length</script>",
        "cases": [
            {"name": "count=3", "assertions": [
                {"kind": "js", "expr": "window.count === 3"},
            ]},
        ],
    },
    {
        "slug": "web-abbr-title",
        "title": "Abbreviation",
        "prompt": "Wrap **HTML** in an `<abbr title=\"HyperText Markup Language\">` element.",
        "starter": "<p>I love HTML</p>",
        "ref": "<p>I love <abbr title='HyperText Markup Language'>HTML</abbr></p>",
        "cases": [
            {"name": "abbr+title", "assertions": [
                {"kind": "selector", "selector": "abbr"},
                {"kind": "attr", "selector": "abbr", "attr": "title", "value": "HyperText Markup Language"},
            ]},
        ],
    },
    {
        "slug": "web-details-summary",
        "title": "Details / summary",
        "prompt": "Render a `<details>` element with a `<summary>` of **More info** and some paragraph text inside.",
        "starter": "",
        "ref": "<details><summary>More info</summary><p>content</p></details>",
        "cases": [
            {"name": "structure", "assertions": [
                {"kind": "selector", "selector": "details summary"},
                {"kind": "text", "selector": "details summary", "text": "More info"},
            ]},
        ],
    },
]

WEB_MEDIUM_2 = [
    {
        "slug": "web-accordion",
        "title": "Accordion",
        "prompt": "Two `<section>` elements each with a `.toggle` button and a `.content` div (starts hidden). Clicking a button toggles its section's `.content` visibility.",
        "starter": "<section><button class='toggle'>A</button><div class='content' hidden>A text</div></section><section><button class='toggle'>B</button><div class='content' hidden>B text</div></section>\n<script>\n</script>",
        "ref": "<section><button class='toggle'>A</button><div class='content' hidden>A text</div></section><section><button class='toggle'>B</button><div class='content' hidden>B text</div></section><script>document.querySelectorAll('.toggle').forEach(b=>b.addEventListener('click',()=>{const c=b.nextElementSibling;c.toggleAttribute('hidden')}))</script>",
        "cases": [
            {"name": "opens",  "assertions": [{"kind": "js", "expr": "document.querySelector('.toggle').click(); !document.querySelector('.content').hasAttribute('hidden')"}]},
            {"name": "closes", "assertions": [{"kind": "js", "expr": "document.querySelector('.toggle').click(); document.querySelector('.toggle').click(); document.querySelector('.content').hasAttribute('hidden')"}]},
        ],
    },
    {
        "slug": "web-password-toggle",
        "title": "Password visibility toggle",
        "prompt": "`#eye` button toggles `#pwd` between `type=password` and `type=text`.",
        "starter": "<input id='pwd' type='password'><button id='eye'>show</button>\n<script>\n</script>",
        "ref": "<input id='pwd' type='password'><button id='eye'>show</button><script>document.getElementById('eye').onclick=()=>{const p=document.getElementById('pwd');p.type=p.type==='password'?'text':'password'}</script>",
        "cases": [
            {"name": "reveals",  "assertions": [{"kind": "js", "expr": "document.querySelector('#eye').click(); document.querySelector('#pwd').type === 'text'"}]},
            {"name": "hides",    "assertions": [{"kind": "js", "expr": "document.querySelector('#eye').click(); document.querySelector('#eye').click(); document.querySelector('#pwd').type === 'password'"}]},
        ],
    },
    {
        "slug": "web-char-counter",
        "title": "Character counter",
        "prompt": "Typing into `#txt` updates `#count` with the current character count.",
        "starter": "<textarea id='txt'></textarea><span id='count'>0</span>\n<script>\n</script>",
        "ref": "<textarea id='txt'></textarea><span id='count'>0</span><script>document.getElementById('txt').addEventListener('input',e=>document.getElementById('count').textContent=e.target.value.length)</script>",
        "cases": [
            {"name": "counts", "assertions": [{"kind": "js", "expr": "const t=document.querySelector('#txt'); t.value='hello'; t.dispatchEvent(new Event('input')); document.querySelector('#count').textContent === '5'"}]},
        ],
    },
    {
        "slug": "web-range-slider-display",
        "title": "Range slider display",
        "prompt": "As `#slider` (range 0-100) moves, `#val` shows the current value.",
        "starter": "<input id='slider' type='range' min='0' max='100' value='50'><span id='val'>50</span>\n<script>\n</script>",
        "ref": "<input id='slider' type='range' min='0' max='100' value='50'><span id='val'>50</span><script>document.getElementById('slider').addEventListener('input',e=>document.getElementById('val').textContent=e.target.value)</script>",
        "cases": [
            {"name": "updates", "assertions": [{"kind": "js", "expr": "const s=document.querySelector('#slider'); s.value=75; s.dispatchEvent(new Event('input')); document.querySelector('#val').textContent === '75'"}]},
        ],
    },
    {
        "slug": "web-copy-to-clipboard",
        "title": "Copy to clipboard",
        "prompt": "Clicking `#copy` calls `navigator.clipboard.writeText` with the value of `#src`. Mock clipboard as `window._clip = ''` and override `navigator.clipboard.writeText`.",
        "starter": "<input id='src' value='hello'><button id='copy'>copy</button>\n<script>\nwindow._clip = ''; navigator.clipboard = { writeText: t => { window._clip = t; return Promise.resolve(); } };\n</script>",
        "ref": "<input id='src' value='hello'><button id='copy'>copy</button><script>window._clip='';navigator.clipboard={writeText:t=>{window._clip=t;return Promise.resolve()}};document.getElementById('copy').onclick=()=>navigator.clipboard.writeText(document.getElementById('src').value)</script>",
        "cases": [
            {"name": "copies", "assertions": [{"kind": "js", "expr": "document.querySelector('#copy').click(); window._clip === 'hello'"}]},
        ],
    },
    {
        "slug": "web-checkbox-toggle-all",
        "title": "Check all / uncheck all",
        "prompt": "Checking `#all` checks all `.item` checkboxes; unchecking it unchecks them all.",
        "starter": "<input type='checkbox' id='all'> All<br><input type='checkbox' class='item'> A<input type='checkbox' class='item'> B<input type='checkbox' class='item'> C\n<script>\n</script>",
        "ref": "<input type='checkbox' id='all'> All<br><input type='checkbox' class='item'> A<input type='checkbox' class='item'> B<input type='checkbox' class='item'> C<script>document.getElementById('all').addEventListener('change',e=>{document.querySelectorAll('.item').forEach(c=>c.checked=e.target.checked)})</script>",
        "cases": [
            {"name": "all checked",   "assertions": [{"kind": "js", "expr": "const a=document.querySelector('#all');a.checked=true;a.dispatchEvent(new Event('change'));Array.from(document.querySelectorAll('.item')).every(c=>c.checked)"}]},
            {"name": "all unchecked", "assertions": [{"kind": "js", "expr": "const a=document.querySelector('#all');a.checked=false;a.dispatchEvent(new Event('change'));Array.from(document.querySelectorAll('.item')).every(c=>!c.checked)"}]},
        ],
    },
    {
        "slug": "web-word-counter",
        "title": "Word counter",
        "prompt": "As `#input` textarea changes, show the word count in `#wc`.",
        "starter": "<textarea id='input'></textarea><span id='wc'>0</span>\n<script>\n</script>",
        "ref": "<textarea id='input'></textarea><span id='wc'>0</span><script>document.getElementById('input').addEventListener('input',e=>{const v=e.target.value.trim();document.getElementById('wc').textContent=v?v.split(/\\s+/).length:0})</script>",
        "cases": [
            {"name": "counts", "assertions": [{"kind": "js", "expr": "const t=document.querySelector('#input');t.value='hello world foo';t.dispatchEvent(new Event('input'));document.querySelector('#wc').textContent==='3'"}]},
            {"name": "empty",  "assertions": [{"kind": "js", "expr": "const t=document.querySelector('#input');t.value='';t.dispatchEvent(new Event('input'));document.querySelector('#wc').textContent==='0'"}]},
        ],
    },
    {
        "slug": "web-multi-select-values",
        "title": "Multi-select values",
        "prompt": "Clicking `#get` sets `window.selected` to an array of checked `.opt` checkbox values.",
        "starter": "<input type='checkbox' class='opt' value='a'> a<input type='checkbox' class='opt' value='b'> b<input type='checkbox' class='opt' value='c'> c<button id='get'>get</button>\n<script>\n</script>",
        "ref": "<input type='checkbox' class='opt' value='a'> a<input type='checkbox' class='opt' value='b'> b<input type='checkbox' class='opt' value='c'> c<button id='get'>get</button><script>document.getElementById('get').onclick=()=>{window.selected=Array.from(document.querySelectorAll('.opt:checked')).map(c=>c.value)}</script>",
        "cases": [
            {"name": "collects", "assertions": [{"kind": "js", "expr": "document.querySelectorAll('.opt')[0].checked=true;document.querySelectorAll('.opt')[2].checked=true;document.querySelector('#get').click();JSON.stringify(window.selected)==='[\"a\",\"c\"]'"}]},
        ],
    },
    {
        "slug": "web-local-storage-list",
        "title": "Persist list to localStorage",
        "prompt": "Clicking `#add` appends the `#item` input value to `<ul id='list'>` and saves the list array to `localStorage` under key `items`.",
        "starter": "<input id='item'><button id='add'>Add</button><ul id='list'></ul>\n<script>\n</script>",
        "ref": "<input id='item'><button id='add'>Add</button><ul id='list'></ul><script>const ls='items';document.getElementById('add').onclick=()=>{const v=document.getElementById('item').value;if(!v)return;const li=document.createElement('li');li.textContent=v;document.getElementById('list').appendChild(li);const arr=JSON.parse(localStorage.getItem(ls)||'[]');arr.push(v);localStorage.setItem(ls,JSON.stringify(arr))}</script>",
        "cases": [
            {"name": "adds and saves", "assertions": [{"kind": "js", "expr": "document.querySelector('#item').value='foo';document.querySelector('#add').click();JSON.parse(localStorage.getItem('items')||'[]').includes('foo')"}]},
        ],
    },
    {
        "slug": "web-sticky-header",
        "title": "Sticky header",
        "prompt": "Give `header` `position: sticky` and `top: 0`.",
        "starter": "<header>nav</header><main style='height:2000px'>content</main>\n<style>\n</style>",
        "ref": "<style>header{position:sticky;top:0}</style><header>nav</header><main style='height:2000px'>content</main>",
        "cases": [
            {"name": "sticky", "assertions": [
                {"kind": "js", "expr": "getComputedStyle(document.querySelector('header')).position === 'sticky'"},
                {"kind": "js", "expr": "getComputedStyle(document.querySelector('header')).top === '0px'"},
            ]},
        ],
    },
    {
        "slug": "web-tooltip-hover",
        "title": "CSS tooltip on hover",
        "prompt": "`.tip::after` shows the text from `data-tip` attribute on hover via CSS `content: attr(data-tip)`.",
        "starter": "<span class='tip' data-tip='Hello!'>hover me</span>\n<style>\n</style>",
        "ref": "<style>.tip{position:relative}.tip:hover::after{content:attr(data-tip);position:absolute;top:100%;left:0;background:#333;color:#fff;padding:2px 6px;white-space:nowrap}</style><span class='tip' data-tip='Hello!'>hover me</span>",
        "cases": [
            {"name": "after rule", "assertions": [
                {"kind": "js", "expr": "Array.from(document.styleSheets).some(ss=>{try{return Array.from(ss.cssRules).some(r=>r.selectorText&&r.selectorText.includes('.tip')&&r.selectorText.includes('after'))}catch{return false}})"},
            ]},
        ],
    },
    {
        "slug": "web-smooth-scroll",
        "title": "Smooth scroll to section",
        "prompt": "Clicking `#go` scrolls to `#target` using `scrollIntoView({behavior:'smooth'})`.",
        "starter": "<button id='go'>Go</button><div style='height:2000px'></div><section id='target'>here</section>\n<script>\n</script>",
        "ref": "<button id='go'>Go</button><div style='height:2000px'></div><section id='target'>here</section><script>document.getElementById('go').onclick=()=>document.getElementById('target').scrollIntoView({behavior:'smooth'})</script>",
        "cases": [
            {"name": "scrolls", "assertions": [
                {"kind": "js", "expr": "let called=false;const el=document.querySelector('#target');el.scrollIntoView=()=>{called=true};document.querySelector('#go').click();called"},
            ]},
        ],
    },
    {
        "slug": "web-time-display",
        "title": "Live clock",
        "prompt": "Display the current time (HH:MM:SS) in `#clock`, updating every second via `setInterval`.",
        "starter": "<div id='clock'></div>\n<script>\n</script>",
        "ref": "<div id='clock'></div><script>function t(){const n=new Date();document.getElementById('clock').textContent=[n.getHours(),n.getMinutes(),n.getSeconds()].map(x=>String(x).padStart(2,'0')).join(':')}t();setInterval(t,1000)</script>",
        "cases": [
            {"name": "shows time", "assertions": [
                {"kind": "js", "expr": "/^\\d{2}:\\d{2}:\\d{2}$/.test(document.querySelector('#clock').textContent)"},
            ]},
        ],
    },
    {
        "slug": "web-drag-drop-reorder",
        "title": "Drag & drop reorder (data transfer)",
        "prompt": "Make `<li draggable>` items reorderable: on dragstart store `textContent`, on drop swap textContents.",
        "starter": "<ul id='list'><li draggable='true'>Alpha</li><li draggable='true'>Beta</li><li draggable='true'>Gamma</li></ul>\n<script>\n</script>",
        "ref": "<ul id='list'><li draggable='true'>Alpha</li><li draggable='true'>Beta</li><li draggable='true'>Gamma</li></ul><script>let src;document.querySelectorAll('#list li').forEach(li=>{li.addEventListener('dragstart',e=>{src=li;e.dataTransfer.setData('text',li.textContent)});li.addEventListener('dragover',e=>e.preventDefault());li.addEventListener('drop',e=>{e.preventDefault();const tmp=src.textContent;src.textContent=li.textContent;li.textContent=tmp})})</script>",
        "cases": [
            {"name": "draggable attrs", "assertions": [
                {"kind": "count", "selector": "#list li[draggable]", "count": 3},
            ]},
        ],
    },
    {
        "slug": "web-infinite-scroll-btn",
        "title": "Load more button",
        "prompt": "Clicking `#more` appends 3 new `<li>` items to `#feed` (any text).",
        "starter": "<ul id='feed'></ul><button id='more'>Load more</button>\n<script>\n</script>",
        "ref": "<ul id='feed'></ul><button id='more'>Load more</button><script>let n=0;document.getElementById('more').onclick=()=>{for(let i=0;i<3;i++){const li=document.createElement('li');li.textContent='Item '+(++n);document.getElementById('feed').appendChild(li)}}</script>",
        "cases": [
            {"name": "adds 3", "assertions": [{"kind": "js", "expr": "document.querySelector('#more').click();document.querySelectorAll('#feed li').length===3"}]},
            {"name": "adds 6 on 2nd click", "assertions": [{"kind": "js", "expr": "document.querySelector('#more').click();document.querySelector('#more').click();document.querySelectorAll('#feed li').length===6"}]},
        ],
    },
    {
        "slug": "web-progress-steps",
        "title": "Step progress bar",
        "prompt": "4 steps rendered as `.step` divs. `#next` increments the active step (max 4) adding class `done` to passed steps and `active` to current.",
        "starter": "<div class='step'>1</div><div class='step'>2</div><div class='step'>3</div><div class='step'>4</div><button id='next'>Next</button>\n<script>\n</script>",
        "ref": "<div class='step'>1</div><div class='step'>2</div><div class='step'>3</div><div class='step'>4</div><button id='next'>Next</button><script>let cur=0;const steps=document.querySelectorAll('.step');function upd(){steps.forEach((s,i)=>{s.classList.toggle('done',i<cur);s.classList.toggle('active',i===cur)})}upd();document.getElementById('next').onclick=()=>{if(cur<steps.length-1){cur++;upd()}}</script>",
        "cases": [
            {"name": "first active", "assertions": [{"kind": "js", "expr": "document.querySelectorAll('.step')[0].classList.contains('active')"}]},
            {"name": "next works",   "assertions": [{"kind": "js", "expr": "document.querySelector('#next').click();document.querySelectorAll('.step')[1].classList.contains('active')&&document.querySelectorAll('.step')[0].classList.contains('done')"}]},
        ],
    },
    {
        "slug": "web-custom-event",
        "title": "Custom event",
        "prompt": "Clicking `#fire` dispatches a `CustomEvent('ping', {detail:{msg:'hello'}})` on `document`. A listener sets `window.gotPing` to the event detail's `msg`.",
        "starter": "<button id='fire'>fire</button>\n<script>\n</script>",
        "ref": "<button id='fire'>fire</button><script>document.addEventListener('ping',e=>window.gotPing=e.detail.msg);document.getElementById('fire').onclick=()=>document.dispatchEvent(new CustomEvent('ping',{detail:{msg:'hello'}}))</script>",
        "cases": [
            {"name": "receives event", "assertions": [{"kind": "js", "expr": "document.querySelector('#fire').click(); window.gotPing === 'hello'"}]},
        ],
    },
    {
        "slug": "web-key-combo",
        "title": "Ctrl+Enter submit",
        "prompt": "Pressing Ctrl+Enter inside `#note` sets `window.submitted` to `true`.",
        "starter": "<textarea id='note'></textarea>\n<script>\nwindow.submitted = false;\n</script>",
        "ref": "<textarea id='note'></textarea><script>window.submitted=false;document.getElementById('note').addEventListener('keydown',e=>{if(e.key==='Enter'&&e.ctrlKey)window.submitted=true})</script>",
        "cases": [
            {"name": "ctrl+enter", "assertions": [{"kind": "js", "expr": "document.querySelector('#note').dispatchEvent(new KeyboardEvent('keydown',{key:'Enter',ctrlKey:true,bubbles:true})); window.submitted===true"}]},
            {"name": "enter only", "assertions": [{"kind": "js", "expr": "window.submitted=false;document.querySelector('#note').dispatchEvent(new KeyboardEvent('keydown',{key:'Enter',ctrlKey:false,bubbles:true})); window.submitted===false"}]},
        ],
    },
    {
        "slug": "web-image-lazy",
        "title": "Lazy-loaded image",
        "prompt": "Add `loading=\"lazy\"` to `<img id=\"hero\">`.",
        "starter": "<img id='hero' src='photo.jpg'>",
        "ref": "<img id='hero' src='photo.jpg' loading='lazy'>",
        "cases": [
            {"name": "lazy attr", "assertions": [
                {"kind": "attr", "selector": "#hero", "attr": "loading", "value": "lazy"},
            ]},
        ],
    },
    {
        "slug": "web-json-parse-display",
        "title": "Parse JSON and display",
        "prompt": "Parse the JSON string in `window.data` (`'{\"name\":\"Alice\",\"age\":30}'`) and render `<p id='out'>Name: Alice, Age: 30</p>`.",
        "starter": "<p id='out'></p>\n<script>\nwindow.data = '{\"name\":\"Alice\",\"age\":30}';\n</script>",
        "ref": "<p id='out'></p><script>window.data='{\"name\":\"Alice\",\"age\":30}';const d=JSON.parse(window.data);document.getElementById('out').textContent=`Name: ${d.name}, Age: ${d.age}`</script>",
        "cases": [
            {"name": "parsed", "assertions": [
                {"kind": "text", "selector": "#out", "text": "Name: Alice, Age: 30"},
            ]},
        ],
    },
    {
        "slug": "web-element-count-display",
        "title": "Badge count",
        "prompt": "Clicking `#add` creates a new `<span class='tag'>item</span>` in `#container` and updates `#badge` with the total count.",
        "starter": "<button id='add'>Add</button><div id='container'></div><span id='badge'>0</span>\n<script>\n</script>",
        "ref": "<button id='add'>Add</button><div id='container'></div><span id='badge'>0</span><script>document.getElementById('add').onclick=()=>{const s=document.createElement('span');s.className='tag';s.textContent='item';document.getElementById('container').appendChild(s);document.getElementById('badge').textContent=document.querySelectorAll('.tag').length}</script>",
        "cases": [
            {"name": "badge updates", "assertions": [
                {"kind": "js", "expr": "document.querySelector('#add').click();document.querySelector('#add').click();document.querySelector('#badge').textContent==='2'"},
            ]},
        ],
    },
    {
        "slug": "web-fullscreen-btn",
        "title": "Fullscreen toggle",
        "prompt": "Clicking `#fs` calls `document.documentElement.requestFullscreen()`. Mock it as `window._fs=true`.",
        "starter": "<button id='fs'>Fullscreen</button>\n<script>\nwindow._fs = false; document.documentElement.requestFullscreen = () => { window._fs = true; return Promise.resolve(); };\n</script>",
        "ref": "<button id='fs'>Fullscreen</button><script>window._fs=false;document.documentElement.requestFullscreen=()=>{window._fs=true;return Promise.resolve()};document.getElementById('fs').onclick=()=>document.documentElement.requestFullscreen()</script>",
        "cases": [
            {"name": "called", "assertions": [{"kind": "js", "expr": "document.querySelector('#fs').click(); window._fs===true"}]},
        ],
    },
]

WEB_HARD_2 = [
    {
        "slug": "web-virtual-scroll",
        "title": "Virtual list (fixed rows)",
        "prompt": "Given `window.items` (100 strings), render only items whose index is in the visible range stored in `window.range = [start, end]` (exclusive end) inside `#list`. Call `window.render(start, end)` to update.",
        "starter": "<div id='list'></div>\n<script>\nwindow.items=Array.from({length:100},(_,i)=>'Item '+i);\n</script>",
        "ref": "<div id='list'></div><script>window.items=Array.from({length:100},(_,i)=>'Item '+i);window.render=(s,e)=>{const l=document.getElementById('list');l.innerHTML='';window.items.slice(s,e).forEach(t=>{const d=document.createElement('div');d.textContent=t;l.appendChild(d)})}</script>",
        "cases": [
            {"name": "renders range", "assertions": [
                {"kind": "js", "expr": "window.render(0,5); document.querySelectorAll('#list div').length===5"},
                {"kind": "js", "expr": "window.render(10,13); document.querySelector('#list div').textContent==='Item 10'"},
            ]},
        ],
    },
    {
        "slug": "web-canvas-rect",
        "title": "Canvas rectangle",
        "prompt": "Draw a 100×50 blue filled rectangle at (10,10) on `<canvas id='c'>`.",
        "starter": "<canvas id='c' width='300' height='200'></canvas>\n<script>\n</script>",
        "ref": "<canvas id='c' width='300' height='200'></canvas><script>const ctx=document.getElementById('c').getContext('2d');ctx.fillStyle='blue';ctx.fillRect(10,10,100,50)</script>",
        "cases": [
            {"name": "blue pixel at 60,35", "assertions": [
                {"kind": "js", "expr": "const ctx=document.getElementById('c').getContext('2d');const d=ctx.getImageData(60,35,1,1).data;d[0]===0&&d[2]===255&&d[3]===255"},
            ]},
        ],
    },
    {
        "slug": "web-state-machine",
        "title": "Traffic light state machine",
        "prompt": "A div `#light` cycles red → green → yellow → red on each `#next` click (set its `data-state` and `textContent` to the colour name).",
        "starter": "<div id='light' data-state='red'>red</div><button id='next'>Next</button>\n<script>\n</script>",
        "ref": "<div id='light' data-state='red'>red</div><button id='next'>Next</button><script>const states=['red','green','yellow'];let i=0;document.getElementById('next').onclick=()=>{i=(i+1)%3;document.getElementById('light').dataset.state=states[i];document.getElementById('light').textContent=states[i]}</script>",
        "cases": [
            {"name": "start red",   "assertions": [{"kind": "js", "expr": "document.querySelector('#light').dataset.state==='red'"}]},
            {"name": "→ green",     "assertions": [{"kind": "js", "expr": "document.querySelector('#next').click();document.querySelector('#light').dataset.state==='green'"}]},
            {"name": "→ yellow",    "assertions": [{"kind": "js", "expr": "document.querySelector('#next').click();document.querySelector('#next').click();document.querySelector('#light').dataset.state==='yellow'"}]},
            {"name": "wraps",       "assertions": [{"kind": "js", "expr": "for(let i=0;i<3;i++)document.querySelector('#next').click();document.querySelector('#light').dataset.state==='red'"}]},
        ],
    },
    {
        "slug": "web-pub-sub",
        "title": "Event bus (pub/sub)",
        "prompt": "Implement `window.bus = { on(event, fn), emit(event, data) }`. Test: subscribe to `'msg'` and emit it.",
        "starter": "<script>\n</script>",
        "ref": "<script>window.bus=(()=>{const h={};return{on:(e,fn)=>{(h[e]=h[e]||[]).push(fn)},emit:(e,d)=>{(h[e]||[]).forEach(fn=>fn(d))}}})()</script>",
        "cases": [
            {"name": "subscribe+emit", "assertions": [
                {"kind": "js", "expr": "let got;window.bus.on('msg',d=>got=d);window.bus.emit('msg','hello');got==='hello'"},
            ]},
            {"name": "multiple listeners", "assertions": [
                {"kind": "js", "expr": "let a=0,b=0;window.bus.on('x',()=>a++);window.bus.on('x',()=>b++);window.bus.emit('x');a===1&&b===1"},
            ]},
        ],
    },
    {
        "slug": "web-promise-chain",
        "title": "Promise chain",
        "prompt": "Define `window.process(n)` returning a Promise that: doubles n after 0ms, then adds 1, then multiplies by 3. Final value stored in `window.result`.",
        "starter": "<script>\n</script>",
        "ref": "<script>window.process=n=>Promise.resolve(n).then(x=>x*2).then(x=>x+1).then(x=>{window.result=x*3;return window.result})</script>",
        "cases": [
            {"name": "chains correctly", "assertions": [
                {"kind": "js", "expr": "(async()=>{await window.process(5);return window.result===33})()"},
            ]},
        ],
    },
    {
        "slug": "web-reactive-binding",
        "title": "Reactive data binding",
        "prompt": "Create `window.store = { value: '' }`. Whenever `store.value` is set, update `#display` textContent automatically (use a setter).",
        "starter": "<div id='display'></div>\n<script>\n</script>",
        "ref": "<div id='display'></div><script>let _v='';window.store=Object.defineProperty({},'value',{get:()=>_v,set(v){_v=v;document.getElementById('display').textContent=v}})</script>",
        "cases": [
            {"name": "updates dom", "assertions": [
                {"kind": "js", "expr": "window.store.value='hello'; document.querySelector('#display').textContent==='hello'"},
            ]},
        ],
    },
    {
        "slug": "web-infinite-counter",
        "title": "Animated counter",
        "prompt": "Clicking `#start` animates `#n` counting from 0 to 100 in exactly 1000ms using `requestAnimationFrame`. Store start timestamp in `window.startTime`.",
        "starter": "<button id='start'>Start</button><span id='n'>0</span>\n<script>\n</script>",
        "ref": "<button id='start'>Start</button><span id='n'>0</span><script>document.getElementById('start').onclick=()=>{window.startTime=performance.now();function frame(ts){const p=Math.min((ts-window.startTime)/1000,1);document.getElementById('n').textContent=Math.round(p*100);if(p<1)requestAnimationFrame(frame)}requestAnimationFrame(frame)}</script>",
        "cases": [
            {"name": "starts at 0", "assertions": [{"kind": "js", "expr": "document.querySelector('#n').textContent==='0'"}]},
            {"name": "click fires", "assertions": [{"kind": "js", "expr": "document.querySelector('#start').click();window.startTime>0"}]},
        ],
    },
    {
        "slug": "web-css-grid-areas",
        "title": "CSS grid areas",
        "prompt": "Use named grid areas so: `.header` spans top, `.sidebar` is left, `.main` is right, `.footer` spans bottom.",
        "starter": "<div class='layout'><div class='header'>H</div><div class='sidebar'>S</div><div class='main'>M</div><div class='footer'>F</div></div>\n<style>\n</style>",
        "ref": "<style>.layout{display:grid;grid-template-areas:'header header' 'sidebar main' 'footer footer';grid-template-columns:1fr 3fr}.header{grid-area:header}.sidebar{grid-area:sidebar}.main{grid-area:main}.footer{grid-area:footer}</style><div class='layout'><div class='header'>H</div><div class='sidebar'>S</div><div class='main'>M</div><div class='footer'>F</div></div>",
        "cases": [
            {"name": "grid display", "assertions": [
                {"kind": "js", "expr": "getComputedStyle(document.querySelector('.layout')).display==='grid'"},
            ]},
            {"name": "areas defined", "assertions": [
                {"kind": "js", "expr": "getComputedStyle(document.querySelector('.header')).gridArea.includes('header')"},
            ]},
        ],
    },
    {
        "slug": "web-keyframe-animation",
        "title": "CSS keyframe animation",
        "prompt": "Animate `.spinner` with a `rotate` keyframe (0° → 360°) over 1s infinite.",
        "starter": "<div class='spinner'>◎</div>\n<style>\n</style>",
        "ref": "<style>@keyframes rotate{to{transform:rotate(360deg)}}.spinner{animation:rotate 1s linear infinite}</style><div class='spinner'>◎</div>",
        "cases": [
            {"name": "animation-name", "assertions": [
                {"kind": "js", "expr": "getComputedStyle(document.querySelector('.spinner')).animationName !== 'none'"},
            ]},
            {"name": "infinite", "assertions": [
                {"kind": "js", "expr": "getComputedStyle(document.querySelector('.spinner')).animationIterationCount === 'infinite'"},
            ]},
        ],
    },
    {
        "slug": "web-typewriter-effect",
        "title": "Typewriter effect",
        "prompt": "On load, type the string **Hello, World!** one character at a time (50ms intervals) into `#out`.",
        "starter": "<div id='out'></div>\n<script>\n</script>",
        "ref": "<div id='out'></div><script>const s='Hello, World!';let i=0;const t=setInterval(()=>{document.getElementById('out').textContent+=s[i++];if(i>=s.length)clearInterval(t)},50)</script>",
        "cases": [
            {"name": "eventually complete", "assertions": [
                {"kind": "js", "expr": "(async()=>{await new Promise(r=>setTimeout(r,700));return document.querySelector('#out').textContent==='Hello, World!'})()"},
            ]},
        ],
    },
    {
        "slug": "web-memoize-function",
        "title": "Memoize a function",
        "prompt": "Implement `window.memoize(fn)` which returns a memoized version of `fn` (cache by first argument).",
        "starter": "<script>\n</script>",
        "ref": "<script>window.memoize=fn=>{const c=new Map();return x=>{if(c.has(x))return c.get(x);const r=fn(x);c.set(x,r);return r}}</script>",
        "cases": [
            {"name": "caches", "assertions": [
                {"kind": "js", "expr": "let calls=0;const f=window.memoize(x=>{calls++;return x*2});f(3);f(3);calls===1&&f(3)===6"},
            ]},
            {"name": "different args", "assertions": [
                {"kind": "js", "expr": "const f=window.memoize(x=>x+1);f(1)===2&&f(2)===3"},
            ]},
        ],
    },
    {
        "slug": "web-autocomplete",
        "title": "Autocomplete dropdown",
        "prompt": "Typing into `#q` shows matching items from `window.items=['apple','apricot','banana','blueberry']` as `<li>` in `#suggestions` (case-insensitive prefix match). Clear on empty.",
        "starter": "<input id='q'><ul id='suggestions'></ul>\n<script>\nwindow.items=['apple','apricot','banana','blueberry'];\n</script>",
        "ref": "<input id='q'><ul id='suggestions'></ul><script>window.items=['apple','apricot','banana','blueberry'];document.getElementById('q').addEventListener('input',e=>{const v=e.target.value.toLowerCase();const ul=document.getElementById('suggestions');ul.innerHTML='';if(!v)return;window.items.filter(x=>x.startsWith(v)).forEach(x=>{const li=document.createElement('li');li.textContent=x;ul.appendChild(li)})})</script>",
        "cases": [
            {"name": "filters", "assertions": [
                {"kind": "js", "expr": "const q=document.querySelector('#q');q.value='ap';q.dispatchEvent(new Event('input'));document.querySelectorAll('#suggestions li').length===2"},
            ]},
            {"name": "clears on empty", "assertions": [
                {"kind": "js", "expr": "const q=document.querySelector('#q');q.value='';q.dispatchEvent(new Event('input'));document.querySelectorAll('#suggestions li').length===0"},
            ]},
        ],
    },
    {
        "slug": "web-scroll-progress",
        "title": "Scroll progress bar",
        "prompt": "As the page scrolls, `#bar` width (%) equals `scrollY / (scrollHeight - clientHeight) * 100`. Update on `scroll` event.",
        "starter": "<div id='bar' style='position:fixed;top:0;left:0;height:4px;background:red;width:0'></div><div style='height:3000px'></div>\n<script>\n</script>",
        "ref": "<div id='bar' style='position:fixed;top:0;left:0;height:4px;background:red;width:0'></div><div style='height:3000px'></div><script>window.addEventListener('scroll',()=>{const pct=window.scrollY/(document.documentElement.scrollHeight-window.innerHeight)*100;document.getElementById('bar').style.width=pct+'%'})</script>",
        "cases": [
            {"name": "scroll listener", "assertions": [
                {"kind": "js", "expr": "window.dispatchEvent(new Event('scroll')); typeof document.querySelector('#bar').style.width === 'string'"},
            ]},
        ],
    },
    {
        "slug": "web-calculator",
        "title": "Basic calculator",
        "prompt": "Implement `window.calc(expr)` that evaluates a string expression with `+`, `-`, `*`, `/` and integers (no division by zero). Use `Function` or similar.",
        "starter": "<script>\n</script>",
        "ref": "<script>window.calc=expr=>Function('return '+expr)()</script>",
        "cases": [
            {"name": "add",   "assertions": [{"kind": "js", "expr": "window.calc('2+3')===5"}]},
            {"name": "mixed", "assertions": [{"kind": "js", "expr": "window.calc('10-3*2')===4"}]},
            {"name": "div",   "assertions": [{"kind": "js", "expr": "window.calc('10/2')===5"}]},
        ],
    },
    {
        "slug": "web-observer-badge",
        "title": "Intersection observer badge",
        "prompt": "Use `IntersectionObserver` to add class `visible` to `#box` when it enters the viewport.",
        "starter": "<div id='box' style='margin-top:200vh'>watch me</div>\n<script>\n</script>",
        "ref": "<div id='box' style='margin-top:200vh'>watch me</div><script>new IntersectionObserver(([e])=>{if(e.isIntersecting)document.getElementById('box').classList.add('visible')}).observe(document.getElementById('box'))</script>",
        "cases": [
            {"name": "observer created", "assertions": [
                {"kind": "js", "expr": "typeof IntersectionObserver !== 'undefined'"},
            ]},
        ],
    },
    {
        "slug": "web-deep-clone",
        "title": "Deep clone utility",
        "prompt": "Implement `window.deepClone(obj)` — a deep clone that handles nested objects and arrays (JSON-safe values only).",
        "starter": "<script>\n</script>",
        "ref": "<script>window.deepClone=obj=>JSON.parse(JSON.stringify(obj))</script>",
        "cases": [
            {"name": "clones", "assertions": [
                {"kind": "js", "expr": "const o={a:{b:1},c:[1,2]};const c=window.deepClone(o);c.a.b=99;o.a.b===1"},
            ]},
            {"name": "array", "assertions": [
                {"kind": "js", "expr": "const a=[1,[2,3]];const b=window.deepClone(a);b[1][0]=99;a[1][0]===2"},
            ]},
        ],
    },
    {
        "slug": "web-throttle",
        "title": "Throttle function",
        "prompt": "Implement `window.throttle(fn, ms)` — calls `fn` at most once per `ms` milliseconds.",
        "starter": "<script>\n</script>",
        "ref": "<script>window.throttle=(fn,ms)=>{let last=0;return(...args)=>{const now=Date.now();if(now-last>=ms){last=now;return fn(...args)}}}</script>",
        "cases": [
            {"name": "calls once in window", "assertions": [
                {"kind": "js", "expr": "let n=0;const t=window.throttle(()=>n++,1000);t();t();t();n===1"},
            ]},
        ],
    },
    {
        "slug": "web-regex-highlight",
        "title": "Regex text highlighter",
        "prompt": "Clicking `#run` wraps all occurrences of the pattern in `#pattern` input inside `#text` span with `<mark>` elements.",
        "starter": "<input id='pattern' value='foo'><div id='text'>foo bar foo baz</div><button id='run'>highlight</button>\n<script>\n</script>",
        "ref": "<input id='pattern' value='foo'><div id='text'>foo bar foo baz</div><button id='run'>highlight</button><script>document.getElementById('run').onclick=()=>{const p=document.getElementById('pattern').value;const el=document.getElementById('text');el.innerHTML=el.textContent.replace(new RegExp(p,'g'),m=>`<mark>${m}</mark>`)}</script>",
        "cases": [
            {"name": "two marks", "assertions": [
                {"kind": "js", "expr": "document.querySelector('#run').click();document.querySelectorAll('#text mark').length===2"},
            ]},
        ],
    },
    {
        "slug": "web-form-stepper-multi",
        "title": "Multi-step form",
        "prompt": "3 `.step-page` divs (only first shown). `#next` shows next page, `#prev` shows previous. Use `hidden` attribute.",
        "starter": "<div class='step-page'>Step 1</div><div class='step-page' hidden>Step 2</div><div class='step-page' hidden>Step 3</div><button id='prev' disabled>Prev</button><button id='next'>Next</button>\n<script>\n</script>",
        "ref": "<div class='step-page'>Step 1</div><div class='step-page' hidden>Step 2</div><div class='step-page' hidden>Step 3</div><button id='prev' disabled>Prev</button><button id='next'>Next</button><script>let cur=0;const pages=document.querySelectorAll('.step-page');function upd(){pages.forEach((p,i)=>p.toggleAttribute('hidden',i!==cur));document.getElementById('prev').disabled=cur===0;document.getElementById('next').disabled=cur===pages.length-1}document.getElementById('next').onclick=()=>{if(cur<pages.length-1){cur++;upd()}};document.getElementById('prev').onclick=()=>{if(cur>0){cur--;upd()}}</script>",
        "cases": [
            {"name": "starts page 1",  "assertions": [{"kind": "js", "expr": "!document.querySelectorAll('.step-page')[0].hasAttribute('hidden')&&document.querySelectorAll('.step-page')[1].hasAttribute('hidden')"}]},
            {"name": "next → page 2",  "assertions": [{"kind": "js", "expr": "document.querySelector('#next').click();!document.querySelectorAll('.step-page')[1].hasAttribute('hidden')"}]},
            {"name": "prev → page 1",  "assertions": [{"kind": "js", "expr": "document.querySelector('#next').click();document.querySelector('#prev').click();!document.querySelectorAll('.step-page')[0].hasAttribute('hidden')"}]},
        ],
    },
    {
        "slug": "web-lazy-image-src",
        "title": "Lazy image src swap",
        "prompt": "When `#img` enters the viewport (use IntersectionObserver), set its `src` from `data-src`.",
        "starter": "<img id='img' data-src='real.jpg' src='placeholder.jpg'>\n<script>\n</script>",
        "ref": "<img id='img' data-src='real.jpg' src='placeholder.jpg'><script>new IntersectionObserver(([e],obs)=>{if(e.isIntersecting){const el=e.target;el.src=el.dataset.src;obs.unobserve(el)}}).observe(document.getElementById('img'))</script>",
        "cases": [
            {"name": "data-src present", "assertions": [
                {"kind": "attr", "selector": "#img", "attr": "data-src", "value": "real.jpg"},
            ]},
        ],
    },
    {
        "slug": "web-color-picker-preview",
        "title": "Colour picker preview",
        "prompt": "As `#picker` (input[type=color]) changes, update `#preview` background to the selected colour.",
        "starter": "<input id='picker' type='color' value='#ff0000'><div id='preview' style='width:50px;height:50px'></div>\n<script>\n</script>",
        "ref": "<input id='picker' type='color' value='#ff0000'><div id='preview' style='width:50px;height:50px'></div><script>document.getElementById('picker').addEventListener('input',e=>{document.getElementById('preview').style.background=e.target.value})</script>",
        "cases": [
            {"name": "updates bg", "assertions": [
                {"kind": "js", "expr": "const p=document.querySelector('#picker');p.value='#00ff00';p.dispatchEvent(new Event('input'));document.querySelector('#preview').style.background==='#00ff00'||getComputedStyle(document.querySelector('#preview')).backgroundColor.includes('0, 255')"},
            ]},
        ],
    },
]

GROUPS = [
    (Language.PYTHON, Level.EASY,   PY_EASY + PY_EASY_2),
    (Language.PYTHON, Level.MEDIUM, PY_MEDIUM + PY_MEDIUM_2),
    (Language.PYTHON, Level.HARD,   PY_HARD + PY_HARD_2),
    (Language.WEB,    Level.EASY,   WEB_EASY + WEB_EASY_2),
    (Language.WEB,    Level.MEDIUM, WEB_MEDIUM + WEB_MEDIUM_2),
    (Language.WEB,    Level.HARD,   WEB_HARD + WEB_HARD_2),
]


class Command(BaseCommand):
    help = "Seed the exercise library."

    @transaction.atomic
    def handle(self, *args, **kwargs):
        created = 0
        updated = 0
        for language, level, items in GROUPS:
            for spec in items:
                ex, was_created = Exercise.objects.update_or_create(
                    slug=spec["slug"],
                    defaults=dict(
                        title=spec["title"],
                        language=language,
                        level=level,
                        prompt_md=spec["prompt"],
                        starter_code=spec.get("starter", ""),
                        reference_solution=spec.get("ref", ""),
                        hints=spec.get("hints", []),
                        tags=spec.get("tags", []),
                    ),
                )
                # Reset cases (idempotent)
                ex.test_cases.all().delete()
                for i, c in enumerate(spec["cases"]):
                    TestCase.objects.create(
                        exercise=ex,
                        name=c["name"],
                        stdin=c.get("stdin", ""),
                        expected_stdout=c.get("expected", ""),
                        assertions=c.get("assertions", []),
                        is_hidden=bool(c.get("hidden", False)),
                        ordering=i,
                    )
                if was_created:
                    created += 1
                else:
                    updated += 1
        self.stdout.write(self.style.SUCCESS(
            f"Seeded exercises — created={created}, updated={updated}"
        ))
