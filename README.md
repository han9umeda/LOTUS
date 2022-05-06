# LOTUS (Lightweight rOuTing simUlator with aSpa) README

## What is LOTUS?

LOTUS is a simulator for inter-domain routing on ASPA deployment situation.

## Support Envirionment

LOTUS works on *macOS 12.1 and Python 3.9.10*.
The main component is composed of Python3 and UNIX shell script, so LOTUS probably runs on major UNIX-based OS.

## How to use.

### Initial setting(execute only once)

1. Setting up Python3 environment on your computer.
2. LOTUS uses pyyaml, so you should install pyyaml (for example `$ pip install pyyaml`).

### Start

`$ python main.py `

LOTUS has interactive UI.
When started, LOTUS outputs intro message and `LOTUS >> ` prompt.
LOTUS support command Tab completion.
If you want to get command list, please pless Tab key twice.

### `expect_for_LOTUS.sh` Script

If you want to execute batch processing, please use `expect` command.
This tool provide a simple script from command list text to expect command format script, `expect_for_LOTUS.sh`.
Write command list, and execute like this

` $ cat [command list file] | ./expect_for_LOTUS.sh`

## Tutorial

Let's start to route exchange simulation.

First of all, you need to define these situation.

 - AS
 - connection between ASes
 - published ASPA
 - ASPV deployed
 - advertising (init/update) messages

After that, start the simulation to execute "run" command.
The result can be seen by "showASList" command.

### Standard Use

Sample situation script is prepared in `sample` directory.
Situation image is `situation_image.png`.
You can execute the script in two ways.

 - execute `$ python main.py` and input commands by hand (like `LOTUS >> addAS 1`, `LOTUS >> addAS 10`, ...)
 - generate batch script to use `expect_for_LOTUS.sh` (like `$ cat sample_situation | ../expect_for_LOTUS.sh > sample_situation.sh`) and execute it

All output is printed to standard output, so if you want to correct simulation result, use shell redirect function or export to a file command like `tee`.

### Import/Export function

LOTUS has situation import/export function.
You can save situation you made in file.

1. input situation you mede (like `LOTUS >> addAS 1`, ... `LOTUS >> addConnection down 1 10`, ... `LOTUS >> autoASPA 100 1`, ...)
2. execute "export" command BEFORE "run" command (like `LOTUS >> export sample_situation.yml`)
3. When you want to simulate the exported situation, execute "import" command and "run" command.

Export file is YAML format text file.
You can also edit the file directly.
