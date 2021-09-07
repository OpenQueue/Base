# -*- coding: utf-8 -*-

import unittest
import sys

# Ignore wildcard imports for unit tests.
from OpenQueue.tests import *  # noqa: F401, F403

"""NOTE
Expects database to be empty!
"""


if __name__ == "__main__":
    # Don't let unittest process any paramters!
    unittest.main(argv=[sys.argv[0]])
