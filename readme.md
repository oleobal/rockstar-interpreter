### An interpreter for the Rockstar programming language

This is a line-by-line interpreter, for [Rockstar](https://github.com/dylanbeattie/rockstar/), in Python 3.

Is it a virtual machine running in a virtual machine ? Yes.


### Operation

`python3 rockstar.py [input.rock]`

Since this is line-per-line interpretation, an interactive mode is available : just run the executable without an input file.

### Inner workings

The entry function is `processProgram`.

Each line is fed to the `tokenize` function, which returns a crude AST.

Then, it is sent to `processInstruction`, which executes the instruction, making use of the `evaluate` function to reduce expressions and get variable values. Each reads or writes to a single context.

The exception is for blocks, which are sent (as text) to `processLineBlock` instead, basically a recursive version of `processProgram`. Blocks are only executed once they are finished.


### Non-conformities

This is compared to the copy of the specification in this repository (`specification.md`), not the official one; this is just to avoid chasing a moving target. We are, of course, planning on making this list empty.

 - Arithmetic is not fully functional yet
 - Comparison is not fully functional yet
 - Listening to `stdin` is not implemented (printing to `stdout` is)
 - Else blocks are not implemented
 - Functions are not implemented
 - Text preprocessing is crude, and in particular targets even what is inside `""` quotes, which means string literals can get changed by the preprocessor (single quotes, for instance, are removed). The problem here is that to identify string literals means we have to already largely tokenize everything, to identify what is a string literal, because of poetic string literals.
 - "inclusive" pronouns are present but not enabled. We are planning on an option to enable them.
 - Type handling is largely ignored, but this is also because there is no way to manipulate types in the language, so that is a moot point.

### Spec Interpretations

The specification can be woefully unclear as to what exactly some things mean or how they are supposed to behave. Here are assumptions made.

 - Functions can only be defined at top level
 - Functions can not be defined if the identifier already is a variable, and vice versa
 - `break` and `continue` behave as in Python
 - commas `,` are puzzling in the spec.

### Venues for improvement

We are trying to get feature complete as fast as possible, and then solve the issues uncovered along the way.

 - Error handling is poor, we should instead throw errors and handle them at the top level which would enable us to display line levels
 - Last named variable (for pronouns) is currently handled manually but a good way would be to have context be a "smart" object updating this field whenever a variable is requested of it (alternatively, make the tokenizer context-aware for this, and replace it on tokenization ?)
 - Numbers are just python floats, which might or might not correspond to the spec
 - Many syntax errors are just ignored in the tokenizer, when they could be caught there and not later.
 
### License

This program is free software: you can redistribute it and/or modify it under the terms of the GNU General Public License as published by the Free Software Foundation, either version 3 of the License, or (at your option) any later version.

This program is distributed in the hope that it will be useful, but WITHOUT ANY WARRANTY; without even the implied warranty of MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the GNU General Public License for more details.

You should have received a copy of the GNU General Public License along with this program.  If not, see <https://www.gnu.org/licenses/>.
