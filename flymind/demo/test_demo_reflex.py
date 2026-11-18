"""Nagrywanie nic nie zmienia: próba z hakami Rec = próba bez nich (ruch łokcia i nadgarstka co do bitu).
Uruchom: .venv/bin/python -I -B flymind/demo/test_demo_reflex.py"""
import os
import sys

sys.dont_write_bytecode = True
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import demo_reflex as DR  # noqa: E402


class NullVid:
    n = 0

    def write(self, f):
        self.n += 1


if __name__ == "__main__":
    box = [None]
    DR.install(box)
    a = DR.run_one(1.0, "N", 0, 0, None, box)
    v = NullVid()
    rec = DR.Rec(v, "test", None)
    b = DR.run_one(1.0, "N", 0, 0, rec, box)
    rec.close()
    keys = ("valid", "dq1", "dq2", "dq3_lev", "palm_at_handover")
    assert [a.get(k) for k in keys] == [b.get(k) for k in keys], (a, b)
    assert v.n > 50 and a["dq2"] < -0.02 and a["dq3_lev"] > 0.02, (v.n, a)
    print("OK", {k: a.get(k) for k in keys}, "klatek", v.n)
