# LOTUS (Lightweight rOuTing simUlator with aSpa) README

## What is LOTUS?

LOTUS is a simulator for inter-domain routing on ASPA deployment situation.

## Support Envirionment

LOTUS works on *macOS 12.1 and Python 3.9.10*.
The main component is composed of Python3 and UNIX shell script, so LOTUS probably runs on major UNIX-based OS.

## How to use.

### Initial setting(execute only once)

1. Setting up Python3 environment on your computer.
2. LOTUS uses pyyaml, so you should install pyyaml(for example `$ pip install pyyaml`).

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
