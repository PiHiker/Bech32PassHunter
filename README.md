# BIP39PassHunter

[![Python](https://img.shields.io/badge/Python-3.7%2B-blue.svg)](https://www.python.org/)
[![License: MIT](https://img.shields.io/badge/License-MIT-green.svg)](LICENSE)
![Bruteforce](https://img.shields.io/badge/Focus-Brute%20Force-orange)
![Bech32](https://img.shields.io/badge/Bitcoin-Bech32-yellow)

**Bech32PassHunter** is a high-performance Python tool for brute-forcing passphrases from a wordlist to derive Bech32 Bitcoin addresses using a known mnemonic phrase. With multiprocessing and real-time progress updates, it’s built for fast, repeatable recovery workflows.

> **Use responsibly.** This tool is for ethical recovery of wallets you own or have explicit permission to access.

---

## ✨ Highlights

- **Mnemonic-based address derivation** using BIP-84 (Bech32).
- **Multiprocessing performance** with automatic CPU core usage.
- **Live progress metrics** (speed, remaining, ETA).
- **Configurable CLI** for wordlists, workers, and update cadence.
- **Fail-fast discovery**: stops immediately when a passphrase is found.

---

## 🚀 Quick Start

```bash
python3 Bech32PassHunter.py \
  --mnemonic "word1 word2 ..." \
  --target-address bc1... \
  --wordlist-path /path/to/wordlist.txt
```

---

## 📦 Installation

1. **Clone the repo**

```bash
git clone https://github.com/PiHiker/Bech32PassHunter.git
cd Bech32PassHunter
```

2. **Install dependencies**

**Option 1 (Recommended): Virtual Environment**

```bash
python3 -m venv venv
source venv/bin/activate
pip install -r requirements.txt
```

**Option 2: Direct Install**

```bash
pip install -r requirements.txt --break-system-packages
```

---

## 🧰 Usage

Run with defaults:

```bash
python3 Bech32PassHunter.py
```

Override key parameters:

```bash
python3 BIP39PassHunter.py \
  --mnemonic "word1 word2 ..." \
  --target-address bc1... \
  --wordlist-path /path/to/wordlist.txt \
  --workers 8 \
  --update-interval 1.5
```

View all options:

```bash
python3 BIP39PassHunter.py -h
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

## 🔍 How It Works

1. Loads passphrases from the wordlist.
2. Derives a Bech32 (BIP-84) address for each passphrase.
3. Compares each derived address to the target.
4. Stops immediately if a match is found.

---

## 📊 Real-Time Progress Example

```
Chunks created: 8, Chunk size: 33
Processed: 229/262 | Remaining: 33 | Words/sec: 113.48 | Time Elapsed: 0h:00m:02s | Estimated Time Remaining: 0h:00m:00s

Passphrase found: password
```

---

## 🗂 Project Layout

```
.
├── BIP39PassHunter.py    # Main script
├── fasttrack.txt         # Example wordlist
├── requirements.txt      # Python dependencies
└── README.md
```

---

## ⚠️ Responsible Use

This project is intended for ethical use only. Only attempt to recover wallets you own or have explicit permission to access. Unauthorized access is illegal and unethical.

---

## 🧩 Limitations

- Performance depends on CPU capability and wordlist size.
- Wordlists must be correctly formatted (one passphrase per line).
- Target mnemonics must match the derivation scheme (BIP-84).

---

## 📝 License

This project is licensed under the MIT License. See the [LICENSE](LICENSE) file for details.
