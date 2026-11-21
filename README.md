# Bech32PassHunter

[![Python 3](https://img.shields.io/badge/Python-3-blue.svg)](https://www.python.org/)
[![License: MIT](https://img.shields.io/badge/License-MIT-green.svg)](LICENSE)
![Bruteforce](https://img.shields.io/badge/Focus-Brute%20Force-orange)
![Bech32](https://img.shields.io/badge/Bitcoin-Bech32-yellow)

**Have your Bitcoin recovery words but forgot the optional passphrase?** Bech32PassHunter checks a local list of passphrases you remember against your wallet’s first BIP84 receiving address. A match confirms that your words and that passphrase reproduce the address. No balance lookup is needed.

**Works offline.** Download and install the tool first. On Linux, use `./offline.sh` to run it without an internet connection even if the computer stays online. On other systems, disconnect before entering wallet information. Neither address verification nor passphrase checking needs a Bitcoin node or block explorer.

[Wallet compatibility](#is-this-the-right-tool-for-my-wallet) · [Public demo](#install-and-try-the-public-demo) · [Offline setup](#offline-setup) · [CLI options](#cli-options) · [Reading the output](#reading-the-output)

**Why “Bech32”?** Bech32 is the encoding of the address used for comparison. The passphrase belongs to BIP39, not Bech32. It is separate from the mnemonic words and from a wallet app’s PIN or file password.

<a id="check-whether-your-wallet-fits"></a>

## Is this the right tool for my wallet?

**Not sure where to start?** Run `python3 Bech32PassHunter.py` with no arguments.
It shows the available paths without asking for wallet data or installing dependencies.

A BIP39 wallet can accept your recovery words and still open a different wallet from the one you expected. A different passphrase produces a different seed, not a “wrong password” message. An address you saved from the original wallet gives you something to compare.

| Your situation | What to do |
| --- | --- |
| You have all your recovery words, a few possible passphrases, and the first receiving address from your original wallet. | Check the address requirements below. If they fit, use [passphrase recovery](#passphrase-recovery). |
| You have an address from an old invoice and an account public export (zpub), but don’t know the receiving index. | Use [`verify-address`](#have-the-account-public-export-check-that-first) without entering recovery words. If it matches at index 7, for example, the address belongs to that account but is not its first receiving address. |
| Your hardware wallet still works and you want to verify a backup before replacing it. | Start with the device’s own backup check if it supports what you need to verify. Typing recovery words into a computer exposes them outside the hardware wallet. |
| You’re missing recovery words or forgot the wallet app’s PIN or file password. | This tool does not recover those. It checks the separate BIP39 passphrase. |

Passphrase recovery compares one address per entry: `m/84'/0'/0'/0/0`, the first external receiving address in account zero. That address starts with `bc1q`, but the prefix alone does not establish the derivation path. A later receiving address, a change address, or a different account can give a negative result even with the correct passphrase. Taproot (`bc1p`, **Bech32m**) is outside this tool’s scope.

**Before trusting “not found”:** confirm the address came from that exact path. Also, this version trims leading and trailing whitespace from each entry, so it cannot check a passphrase that intentionally starts or ends with a space.

## Install and try the public demo

From a terminal with Python 3:

```sh
git clone https://github.com/PiHiker/Bech32PassHunter.git
cd Bech32PassHunter
python3 -m venv .venv
source .venv/bin/activate
python -m pip install -r requirements.txt
```

You can now turn off Wi-Fi and unplug Ethernet. Try the public demo while disconnected:

```sh
python Bech32PassHunter.py --demo
```

The demo uses public example data and the included `fasttrack.txt`. Run it from the repository directory. To inspect the available options without installing dependencies, run `python3 Bech32PassHunter.py --help`.

A successful demo ends with `Passphrase found (hidden).` This checks that the installation works with the bundled example. It does not test your wallet.

### Offline setup

**To block the tool’s network access on Linux:** activate the project virtual environment, then use `./offline.sh` instead of `python Bech32PassHunter.py`. Try it with public data first:

```sh
./offline.sh --demo
```

The launcher uses Linux network namespaces. The script and its worker processes see only an isolated loopback interface, with no route to the internet or LAN. If `unshare` is missing or the kernel disallows unprivileged namespaces, the launcher stops; it never retries without isolation. Running Python directly does **not** enable this protection. This isolates networking, not the filesystem or other software on the computer.

**For a home wallet:** run the demo first. If you have an account public export, start with `./offline.sh verify-address`; you may be able to answer your question without touching the recovery words. Use a trusted local terminal rather than a shared or recorded session. A file containing remembered passphrases is sensitive too: keep it out of cloud-synced folders.

**For a research lab:** use the public demo or synthetic wallet data. The launcher disables ordinary core dumps, sets owner-only default permissions for new files, and starts Python in isolated mode without writing bytecode. It doesn’t change permissions on existing files, remove secrets from memory, or protect a compromised host.

If the wallet computer must **never** go online, prepare the files on a connected computer with the same operating system, processor architecture, and Python version. From the project directory, build a local folder of installable packages:

```sh
python3 -m pip wheel --wheel-dir wheels -r requirements.txt
```

Once that finishes successfully, copy the project files and the `wheels` folder to the offline computer. With Python 3 already installed there, run these commands from the copied project directory:

```sh
python3 -m venv .venv
source .venv/bin/activate
python -m pip install --no-index --find-links=./wheels -r requirements.txt
python Bech32PassHunter.py --demo
```

`--no-index` tells pip to install from the local package folder. Keep real recovery words and passphrases off the connected preparation computer. A match checks an address locally; it says nothing about the wallet’s current balance.

## Use your own inputs

### Have the account public export? Check that first

If the wallet gave you a new address each time you clicked **Receive**, use
`python Bech32PassHunter.py verify-address`. Enter the known address and the
account’s mainnet BIP84 **zpub** at the hidden prompts. This local check needs
neither a mnemonic nor a wordlist. A zpub reveals the account’s addresses,
so treat it as private even though it cannot authorize spending.

The command checks receiving indexes 0 through 19 in that account and reports
the matching index. Use `--count N` to check just the first N (1 to 20).
A miss says nothing about change addresses, other accounts, or later indexes.
This mode accepts account-level zpubs, not descriptors, xpubs, or private keys.

### Passphrase recovery

Supply the known receiving address with `--target-address` and a local UTF-8 file with `--wordlist-path`, one candidate per line. Enter the mnemonic at the hidden terminal prompt. It is not accepted as a command-line argument.

The tool checks the address format and checksum before prompting for the mnemonic. It then validates the BIP39 words and checksum locally before starting workers. These checks catch input mistakes; they cannot confirm that an address belongs to a particular wallet.

A match prints `Passphrase found (hidden).` If you need to see the value, choose `--show-passphrase` before starting. It only reveals the result when output goes to a terminal. A terminal recorder can still capture visible text.

## How it works

1. The tool reads the candidate file and divides its lines among local worker processes.
2. For each line, it combines the passphrase with the mnemonic to derive a seed. It then derives the first BIP84 receiving address from that seed.
3. It compares the derived address with the address you supplied. The address is the check: a different passphrase can produce a valid wallet, just not the one you expected. No balance lookup is involved.

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
| `0` | Match found, or the guide or help was displayed. |
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
