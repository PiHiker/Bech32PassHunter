# Bech32PassHunter

[![Python](https://img.shields.io/badge/Python-3.7%2B-blue.svg)](https://www.python.org/)
[![License: MIT](https://img.shields.io/badge/License-MIT-green.svg)](LICENSE)

**Bech32PassHunter** is a high-performance Python tool designed to brute-force passphrases from a wordlist to derive Bech32 Bitcoin addresses using a known mnemonic phrase. Its multi-threaded design and real-time progress updates make it an efficient solution for recovering lost Bitcoin wallet passphrases.

## Inspiration

This project was inspired by the [Corey Phillips Bitcoin Puzzle](https://privatekeys.pw/puzzles/0.01-btc-corey-phillips-puzzle). The challenge motivated the creation of a tool capable of exploring the possibilities of recovering Bitcoin addresses from a known mnemonic by brute-forcing passphrases.

## Features

- **Mnemonic-based Address Derivation**: Generates Bitcoin addresses using a known mnemonic and passphrases.
- **Brute-Force Capabilities**: Efficiently tests passphrases from a wordlist.
- **Multi-threaded Processing**: Uses all available CPU cores for high performance.
- **Real-time Progress Updates**: Displays progress, speed, elapsed time, and estimated time remaining.
- **Error Handling**: Gracefully handles file errors and exceptions during passphrase processing.
- **Configurable CLI**: Override mnemonic, wordlist, target address, and performance tuning at runtime.

**Note:** This tool is intended for ethical use only, such as recovering lost wallet passphrases. Always ensure you have the right to access the wallets being brute-forced.

## Requirements

- Python 3.7 or higher.
- The following Python libraries (listed in `requirements.txt`):
  - `bip-utils`
  - `multiprocessing`

## Installation

1. Clone the repository and change to directory:

git clone https://github.com/PiHiker/Bech32PassHunter.git 

cd Bech32PassHunter

2. Install dependencies:

Option 1: Use a Virtual Environment (Recommended)
Create a virtual environment in your project directory:

python3 -m venv venv

Activate the virtual environment:

source venv/bin/activate

You should see (venv) at the beginning of your terminal prompt, indicating the virtual environment is active. 
Then, install dependencies:

pip install -r requirements.txt

Option 2: Install Directly

If you want to bypass the virtual environment, run:

pip install -r requirements.txt --break-system-packages

## Quick Start

```bash
python3 Bech32PassHunter.py \
  --mnemonic "word1 word2 ..." \
  --target-address bc1... \
  --wordlist-path /path/to/wordlist.txt
```

## Usage

Run the script with:

python3 Bech32PassHunter.py

You can also override defaults via CLI flags:

```bash
python3 Bech32PassHunter.py \
  --mnemonic "word1 word2 ..." \
  --target-address bc1... \
  --wordlist-path /path/to/wordlist.txt \
  --workers 8 \
  --update-interval 1.5
```

Use `-h` to see all available options:

```bash
python3 Bech32PassHunter.py -h
```


## Configuration

Before running the script, you can customize the following variables inside the script or use the CLI options above:

- **`mnemonic_phrase`**: Replace with your known 12, 15, 18, 21, or 24-word mnemonic phrase.
- **`target_address`**: Replace with the Bech32 Bitcoin address you are attempting to recover.
- **`wordlist_path`**: Replace with the path to your wordlist file.
- **`workers`**: Tune how many CPU processes to use.
- **`update_interval`**: Control how often progress updates are printed.
- **`chunk_size`**: Override how many passphrases each worker processes at a time.

## How It Works

1. The script reads passphrases from the wordlist file.
2. It generates Bitcoin addresses using the BIP-84 standard for each passphrase.
3. It compares the generated address with the target address.
4. If a match is found, the passphrase is displayed and the process is terminated.
5. If no match is found, it completes processing the entire wordlist.

## Real-time Progress Example

As the script runs, you'll see real-time updates like this:

python3 Bech32PassHunter.py

Chunks created: 8, Chunk size: 33
Processed: 229/262 | Remaining: 33 | Words/sec: 113.48 | Time Elapsed: 0h:00m:02s | Estimated Time Remaining: 0h:00m:00s

Passphrase found: password

## Project Layout

```
.
├── Bech32PassHunter.py   # Main script
├── fasttrack.txt         # Example wordlist
├── requirements.txt      # Python dependencies
└── README.md
```

## Responsible Use

This project is intended for ethical use only. Only attempt to recover wallets you own or have explicit permission to access.

## Limitations

- Performance depends on CPU capabilities and the size of the wordlist.
- Wordlists must be compatible and formatted correctly (one passphrase per line).
- The target mnemonic must match the derivation scheme (BIP-84 in this case).

## Ethical Disclaimer

This tool is intended solely for ethical purposes, such as recovering access to your own Bitcoin wallets. Unauthorized use to access wallets without permission is illegal and unethical.

## License

This project is licensed under the MIT License. See the LICENSE file for details.
