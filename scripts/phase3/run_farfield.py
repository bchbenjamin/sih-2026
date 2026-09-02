#!/usr/bin/env python3
from farfield_driver import main

if __name__ == "__main__":
    import sys
    sys.argv[1:1] = ["--scenario", "hybrid"]
    main()
