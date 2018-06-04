import os
import sys

os.system("python setup.py sdist upload")
os.system(f"git commit -am '{sys.argv[1]}' ")
os.system("git push")
