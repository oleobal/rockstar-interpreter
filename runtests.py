# Runs a set of tests to quickly check we didn't break anything


import argparse
argparser = argparse.ArgumentParser(description="Will execute .rock files that have a corresponding .expected-output files and compare their output to that.")
argparser.add_argument('-s', '--stopOnError',   action='store_true', help='stop on error',                       default=False)
argparser.add_argument('-c', '--colors',        action='store_true', help='use ANSI coloring markers in output', default=False)
argparser.add_argument('-d', '--displayErrors', action='store_true', help='display errors as they happen',       default=False)
argparser.add_argument('-l', '--location',      type=str,            help='set where to look for scripts',       default="scripts")
argparser.add_argument('-p', '--program',       type=str,            help='set program to execute interpreter',  default="python.exe")
argparser.add_argument('-i', '--interpreter',   type=str,            help='set interpreter file',                default="rockstar.py")

args = argparser.parse_args()


from os import listdir
files = listdir(args.location)
targets = []
for i in files :
	if i[-5:] == ".rock":
		name = i[:-5]
		if (name+".expected-output") in files :
			targets.append(name)

targets = sorted(targets)

import subprocess

if args.displayErrors:
	err = None
else:
	err=subprocess.DEVNULL

colorOK = ""
colorERR= ""
colorEND= ""
if args.colors:
	colorOK = "\033[92m"
	colorERR= "\033[91m"
	colorEND= "\033[0m"

passed = 0
for t in targets :
	result = subprocess.run([args.program, args.interpreter, (args.location+"/"+t+".rock")], stdout=subprocess.PIPE, stderr=err)
	out = result.stdout.decode('utf-8')
	out = "\n".join(out.splitlines()) # windows, but this also removes empty lines FIXME
	
	with open(args.location+"/"+t+".expected-output", 'r') as f:
		expectedOut = f.read()
	
	if out == expectedOut:
		print(colorOK+"OK ",t, colorEND)
		passed += 1
	else:
		print(colorERR+"ERR",t, colorEND)
		if args.displayErrors:
			print("Expected :")
			print(repr(expectedOut))
			print("Got :")
			print(repr(out))
		if args.stopOnError :
			break

if passed == len(targets):
	print("ALL tests passed")
else:
	print("{0} / {1} tests passed".format(passed, len(targets)))