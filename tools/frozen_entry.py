"""Standalone entry point, including a deterministic local diagnostic mode."""
import multiprocessing
import sys


if __name__=='__main__':
    multiprocessing.freeze_support()
    if '--self-test' in sys.argv:
        from frozen_diagnostics import run
        raise SystemExit(run(sys.argv[sys.argv.index('--self-test')+1]))
    from app import main
    main()
