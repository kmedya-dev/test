import sys
sys.stdout.write('First line\n')
sys.stdout.write('Second line\n')
sys.stdout.write('\x1b[A')
sys.stdout.write('OVERWRITE')
sys.stdout.flush()
