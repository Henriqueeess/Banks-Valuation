"""Run the full pipeline: fetch -> transform -> model -> report.

    python run.py            # everything
    python run.py --skip-fetch
"""
import sys

from src import fetch, model, report, transform

if __name__ == "__main__":
    if "--skip-fetch" not in sys.argv:
        fetch.main()
    transform.main()
    model.main()
    report.main()
