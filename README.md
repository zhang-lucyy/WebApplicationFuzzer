# Fuzzer

## Description
Web application fuzzer project for SWEN331 Fall '24.

## Installation
1. Make sure you have python and dvwa installed.
2. Install MechanicalSoup and argparse using pip3.

## Usage
Part 1 - Discover

To run the discover command on DVWA or another web page, run these following commands:
- python3 fuzzer.py discover http://localhost/ --custom-auth=dvwa --common-words=words.txt --extensions=extensions.txt
- python3 fuzzer.py discover http://127.0.0.1/fuzzer-tests/ --common-words=words.txt

*--custom-auth=dvwa only applies to DVWA, additionally --common-words is required but you may omit --extensions if you please*

