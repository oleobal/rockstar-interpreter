# Runs a set of tests to quickly check we didn't break anything

program = "python.exe"
file = "rockstar.py"
argLocation = "scripts/"

stopOnError = False
displayError = False

arguments = [

{"file":"test.rock",
"expectedOut":
"""meaning your love
3.14
669.14
True
Jojo
Arithmetic for rockstars
Add 2 3
5.0
5.0
Mul 2 3
6.0
Div 3 2
1.5
Sub 2 3
-1.0
3.0"""},

{"file":"test-proper-variables.rock",
"expectedOut":
"""28.0"""},

{"file":"test-poetic-assign.rock",
"expectedOut":
"""447.0
you are mine..come home and says you not worth it"""},

{"file":"test-blocks.rock",
"expectedOut":
"""Hello
Let is spend some time together
Sweet Sixteen
I love you
8.0
I love you
7.0
I love you
6.0
I love you
5.0
I love you
4.0
I love you
3.0
I love you
2.0
I love you
1.0
Goodbye"""},

{"file":"test-blocks-2.rock",
"expectedOut":
"""439.0
Hey Hey
438.0
Hey Hey
437.0
Hey Hey
436.0
Hey Hey
435.0
Hey Hey
434.0
Hey Hey
433.0
Hey Hey
432.0
Hey Hey
431.0
Hey Hey
430.0
Hey Hey
429.0
Hey Hey
428.0
Hey Hey
427.0
Hey Hey
426.0
Hey Hey
405.0
Hey Hey
404.0
Hey Hey
403.0
402.0
Hey Hey
401.0"""}
]

import subprocess
for a in arguments :
	result = subprocess.run([program, file, argLocation+a["file"]], stdout=subprocess.PIPE)
	out = result.stdout.decode('utf-8')
	out = "\n".join(out.splitlines()) # windows, but this also removes empty lines FIXME
	
	if out == a["expectedOut"]:
		print("OK ",a["file"])
	else:
		print("ERR",a["file"])
		if displayError:
			print("Expected :")
			print(repr(a["expectedOut"]))
			print("Got :")
			print(repr(out))
		if stopOnError :
			break
			
		