"""Krok 5b — ta sama próba nadgarstka co reflex5.py, z JEDNĄ zmianą: próg oddania dłoni F_ON 3 N zamiast 1 N.
Uzasadnienie (wniosek PO teście r1, oznaczony jako hipoteza): w 6 z 10 porażek W5 nacisk dłoni w chwili oddania był >1 N,
ale spadał do 0,05–0,67 N w ciągu 0,5 s, a nadgarstek się nie ruszał. Reszta kodu i kryteriów bez zmian.
Uruchom jak reflex5.py (--net N|F|L, --glu, --seed, --poses, --tag, --out). Ziarna testowe 21801 tylko z STEP5B_FINAL_TEST=1."""
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import reflex as R    # noqa: E402
import reflex5 as R5  # noqa: E402

R.F_ON = 3.0          # R5.trial5 czyta R.F_ON w chwili wywołania — ta sama moduł-obiekt

if __name__ == "__main__":
    if "--seed" in sys.argv and int(sys.argv[sys.argv.index("--seed") + 1]) == 21801 and not os.environ.get("STEP5B_FINAL_TEST"):
        sys.exit("ziarna testowe kroku 5b tylko w teście końcowym (STEP5B_FINAL_TEST=1)")
    R.TwoNet = R5.HeadNet
    R.trial = R5.trial5
    R.main()
