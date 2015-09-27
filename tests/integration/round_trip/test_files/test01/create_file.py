#!/usr/bin/env python
from sys import exit

with open('/tmp/test01_file', 'w') as FILE:
    FILE.write('cats')

exit(0)
