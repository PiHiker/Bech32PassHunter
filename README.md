# Bech32PassHunter

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

## Use your own inputs

Supply the known receiving address with `--target-address` and a local UTF-8 file with `--wordlist-path`, one candidate per line. Enter the mnemonic at the hidden terminal prompt. It is not accepted as a command-line argument.

A match prints `Passphrase found (hidden).` If you need to see the value, choose `--show-passphrase` before starting. It only reveals the result when output goes to a terminal. A terminal recorder can still capture visible text.

| Exit code | Meaning |
| --- | --- |
| `0` | Match found (or help displayed). |
| `1` | Run completed without a match for the supplied inputs. |
| `2` | Input or setup problem. Read the message on standard error. |
| `130` | Interrupted with Ctrl+C. |

If a run finishes without a match, first confirm the known address’s account, receiving index, and network in the original wallet. A negative result does not establish that the mnemonic is wrong.

[MIT license](LICENSE)
