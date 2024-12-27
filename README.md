# Web Application Fuzzer
Fall '24 - SWEN331 Engineering Secure Software

## Description
Developed using Python and the MechanicalSoup package, this fuzzer can identify vulnerabilities in web applications, specifically testing with the Damn Vulnerable Web Application (DVWA). Conducts page and input discovery, link crawling, and testing with fuzz vectors to detect vulnerabilites such as lack of sanitization and sensitive data leaks.

## Installation
1. Make sure you have python and dvwa installed.
2. Install MechanicalSoup and argparse using pip3.

## Usage
Part 1 - Discover

To run the discover command on DVWA or fuzzer-tests, run these following commands:
- python3 fuzzer.py discover http://localhost/ --custom-auth=dvwa --common-words=words.txt --extensions=extensions.txt
- python3 fuzzer.py discover http://127.0.0.1/fuzzer-tests/ --common-words=words.txt

*--custom-auth=dvwa only applies to DVWA, additionally --common-words is required but you may omit --extensions if you please*

Part 2 - Test

To run the test command on DVWA or fuzzer-tests, run these following commands:
- python3 fuzzer.py test http://localhost:8000 --custom-auth=dvwa --common-words=words.txt --vectors=vectors.txt --sensitive=sensitive.txt
- python3 fuzzer.py test http://127.0.0.1/fuzzer-tests/ --common-words=words.txt --vectors=vectors.txt --sensitive=sensitive.txt

Running the test command will automatically run the discover command first. Please note that testing may take a bit to load if the browser has a lot of inputs!

*--vectors=vectors.txt and --sensitive=sensitive.txt are required, --sanitized_chars and --slow are not required so default values will be provided if those parameters are omitted*
