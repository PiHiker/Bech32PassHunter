# Bech32PassHunter

[![Python](https://img.shields.io/badge/Python-3.7%2B-blue.svg)](https://www.python.org/)
[![License: MIT](https://img.shields.io/badge/License-MIT-green.svg)](LICENSE)
![Bruteforce](https://img.shields.io/badge/Focus-Brute%20Force-orange)
![Bech32](https://img.shields.io/badge/Bitcoin-Bech32-yellow)

Fast, multiprocessing brute-force of Bech32 (BIP-84) addresses from a known mnemonic and a passphrase wordlist. Built for focused recovery workflows with clear progress telemetry.

> **Responsible use only.** Recover wallets you own or have explicit permission to access.

---

## Why Bech32PassHunter

- **Speed-first design**: uses all available CPU cores by default.
- **Actionable telemetry**: live stats on speed, progress, and ETA.
- **Simple CLI**: one command to get started, plenty of overrides when needed.

---

## Quick Start

```bash
python3 Bech32PassHunter.py \
  --mnemonic "word1 word2 ..." \
  --target-address bc1... \
  --wordlist-path /path/to/wordlist.txt
```

---

## Installation

Clone the repo:

```bash
git clone https://github.com/PiHiker/Bech32PassHunter.git
cd Bech32PassHunter
```

Install dependencies:

```bash
python3 -m venv venv
source venv/bin/activate
pip install -r requirements.txt
```

If you prefer a direct install:

```bash
pip install -r requirements.txt --break-system-packages
```

---

## Usage

Run with defaults:

```bash
python3 Bech32PassHunter.py
```

Override key parameters:

```bash
python3 Bech32PassHunter.py \
  --mnemonic "word1 word2 ..." \
  --target-address bc1... \
  --wordlist-path /path/to/wordlist.txt \
  --workers 8 \
  --update-interval 1.5
```

Show all options:

```bash
python3 Bech32PassHunter.py -h
```

### CLI Options

| Flag | Default | Description |
| --- | --- | --- |
| `--mnemonic` | Built-in demo mnemonic | Known mnemonic phrase used to derive addresses. |
| `--target-address` | Demo Bech32 address | Target Bech32 Bitcoin address to match. |
| `--wordlist-path` | `fasttrack.txt` | Path to a wordlist (one passphrase per line). |
| `--workers` | CPU count | Number of worker processes to use. |
| `--chunk-size` | Auto-calculated | Override chunk size per worker (0 = auto). |
| `--update-interval` | `2.0` | Seconds between progress updates. |

---

## How It Works

1. Loads passphrases from the wordlist.
2. Derives a Bech32 (BIP-84) address for each passphrase.
3. Compares each derived address to the target.
4. Stops immediately if a match is found.

---

## Progress Output Example

```
Chunks created: 8, Chunk size: 33
Processed: 229/262 | Remaining: 33 | Words/sec: 113.48 | Time Elapsed: 0h:00m:02s | Estimated Time Remaining: 0h:00m:00s

Passphrase found: password
```

---

## Project Layout

```
.
├── Bech32PassHunter.py   # Main script
├── fasttrack.txt         # Example wordlist
├── requirements.txt      # Python dependencies
└── README.md
```

---

## Limitations

- Performance depends on CPU capability and wordlist size.
- Wordlists must be correctly formatted (one passphrase per line).
- Target mnemonics must match the derivation scheme (BIP-84).

---

## License

This project is licensed under the MIT License. See the [LICENSE](LICENSE) file for details.
