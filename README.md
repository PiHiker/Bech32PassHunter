# Bech32PassHunter

[![Python 3](https://img.shields.io/badge/Python-3-blue.svg)](https://www.python.org/)
[![License: MIT](https://img.shields.io/badge/License-MIT-green.svg)](LICENSE)
![Bruteforce](https://img.shields.io/badge/Focus-Brute%20Force-orange)
![Bech32](https://img.shields.io/badge/Bitcoin-Bech32-yellow)

[Wallet compatibility](#check-whether-your-wallet-fits) · [Public demo](#install-and-try-the-public-demo) · [CLI options](#cli-options) · [Reading the output](#reading-the-output)

Check a list of possible **BIP39 passphrases** against your wallet’s first **BIP84 receiving address**. You need the complete mnemonic and a known address from a Bitcoin mainnet wallet you own or are authorized to recover.

**Why “Bech32”?** Bech32 is the encoding of the address used for comparison. The passphrase belongs to BIP39, not Bech32. It is separate from the mnemonic words and from a wallet app’s PIN or file password.

## Check whether your wallet fits

This tool compares one address per entry: `m/84'/0'/0'/0/0`, the first external receiving address in account zero. That address starts with `bc1q`, but the prefix alone does not establish the derivation path. A later receiving address, a change address, or a different account can give a negative result even with the correct passphrase. Taproot (`bc1p`, **Bech32m**) is outside this tool’s scope.

## Install and try the public demo

From a terminal with Python 3:

```sh
git clone https://github.com/PiHiker/Bech32PassHunter.git
cd Bech32PassHunter
python3 -m venv .venv
source .venv/bin/activate
python -m pip install -r requirements.txt
python Bech32PassHunter.py --demo
```

The demo uses public example data and the included `fasttrack.txt`. Run it from the repository directory. To inspect the available options without installing dependencies, run `python3 Bech32PassHunter.py --help`.

A successful demo ends with `Passphrase found (hidden).` This checks that the installation works with the bundled example. It does not test your wallet.

## Use your own inputs

Supply the known receiving address with `--target-address` and a local UTF-8 file with `--wordlist-path`, one candidate per line. Enter the mnemonic at the hidden terminal prompt. It is not accepted as a command-line argument.

The tool checks the address format and checksum before prompting for the mnemonic. It then validates the BIP39 words and checksum locally before starting workers. These checks catch input mistakes; they cannot confirm that an address belongs to a particular wallet.

A match prints `Passphrase found (hidden).` If you need to see the value, choose `--show-passphrase` before starting. It only reveals the result when output goes to a terminal. A terminal recorder can still capture visible text.

## How it works

1. The tool reads the candidate file and divides its lines among local worker processes.
2. For each line, it combines the passphrase with the mnemonic to derive a seed. It then derives the first BIP84 receiving address from that seed.
3. It compares the derived address with the address you supplied. The address is the check: a different passphrase can produce a valid wallet, just not the one you expected. No balance lookup is involved.

**Whitespace matters:** the current reader strips spaces and other whitespace from the beginning and end of each line. A passphrase that intentionally begins or ends with a space cannot be checked exactly by this version.

## CLI options

| Option | Default | What it controls |
| --- | --- | --- |
| `--demo` | Off | Uses the public example mnemonic instead of the hidden prompt. |
| `--target-address` | Required outside demo mode | Known first receiving address. The demo supplies its own if omitted. |
| `--wordlist-path` | `fasttrack.txt` | UTF-8 text file, one candidate per line. Relative paths start in the current directory. |
| `--show-passphrase` | Off | Displays a match only if standard output is a terminal. |
| `--workers` | CPU count | Number of worker processes, capped at the number of input lines. |
| `--chunk-size` | `0` (automatic) | Number of lines in each work chunk. |
| `--update-interval` | `2.0` seconds | Time between progress updates. |
| `-h`, `--help` | | Prints usage and exits without prompting for a mnemonic. |

## Reading the output

A public demo run can look like this. Counts and timing vary:

```text
Chunks created: 8, Chunk size: 33
Processed: 100/262 | Remaining: 162 | Words/sec: 50.00 | Time Elapsed: 0h:00m:02s | Estimated Time Remaining: 0h:00m:03s

Passphrase found (hidden).
```

Workers report progress in batches, so the counter can pause or jump. A match can end the run before the counter reaches the total. Use the final message and exit code to interpret the result.

| Exit code | Meaning |
| --- | --- |
| `0` | Match found (or help displayed). |
| `1` | Run completed without a match for the supplied inputs. |
| `2` | Input, setup, or worker error. An incomplete check is not a negative result. See standard error. |
| `130` | Interrupted with Ctrl+C. |

If a run finishes without a match, first confirm the known address’s account, receiving index, and network in the original wallet. A negative result does not establish that the mnemonic is wrong.

## Repository guide

| File | Purpose |
| --- | --- |
| [`Bech32PassHunter.py`](Bech32PassHunter.py) | CLI, address derivation, worker processes, and result reporting. |
| [`fasttrack.txt`](fasttrack.txt) | Example input used by the public demo. |
| [`requirements.txt`](requirements.txt) | Python dependency for wallet derivation. |
| [`LICENSE`](LICENSE) | MIT license. |
