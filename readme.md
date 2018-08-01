### An interpreter for the Rockstar programming language

This is a line-by-line interpreter, for [Rockstar](https://github.com/dylanbeattie/rockstar/), in Python 3.

Is it a virtual machine implemented in a virtual machine ? Yes.


### Operation

`python rockstar.py <input.rock>`

Since this is line-per-line interpretation, an interactive mode should not be hard to set up, but this is low priority.

### Inner workings

Each line is fed to the `tokenize` function, which returns a crude AST. Then, it is sent to `processInstruction`, which executes the instruction, making use of the `evaluate` function to reduce expressions and get variable values. Each reads or writes to a single context.

If it is a multiline instruction (block), we block (ha) after the tokenization, growing the AST until we reached root level again, at which point the AST is executed. *(not yet implemented)*


### Venues for improvement

We are trying to get feature complete as fast as possible, and then solve the issues uncovered along the way.

 - Error handling is poor, we should instead throw errors and handle them at the top level which would enable us to display line levels
 - Last named variable (for pronouns) is currently handled manually but a good way would be to have context be a "smart" object updating this field whenever a variable is requested of it (alternatively, make the tokenizer context-aware for this, and replace it on tokenization ?)

### License

This program is free software: you can redistribute it and/or modify
it under the terms of the GNU General Public License as published by
the Free Software Foundation, either version 3 of the License, or
(at your option) any later version.

This program is distributed in the hope that it will be useful,
but WITHOUT ANY WARRANTY; without even the implied warranty of
MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
GNU General Public License for more details.

You should have received a copy of the GNU General Public License
along with this program.  If not, see <https://www.gnu.org/licenses/>.