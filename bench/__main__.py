"""`make bench` entry point (P31). Scores the rule matcher against the draft corpus labels; cost and LLM arms come later."""

import sys

from bench.corpus import score


def main() -> int:
    r = score()
    d = r.pop("disagreements")
    print(f"bench: rule set {r['rule_set']}, labels DRAFT (synthetic corpus)")
    print({k: round(v, 3) if isinstance(v, float) else v for k, v in r.items() if k != "rule_set"})
    for x in d:
        print("  disagreement:", x)
    return 0


if __name__ == "__main__":
    sys.exit(main())
