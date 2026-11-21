import argparse
import getpass
import multiprocessing
import sys
import time
import warnings
from math import ceil, isfinite
from pathlib import Path
from multiprocessing import Manager, Pool

DEFAULT_MNEMONIC_PHRASE = (
    "leopard damp effort face charge exclude pilot drum vanish case volume rude "
    "warfare call sure embrace drive sure update ugly plastic movie resist pill"
)
DEFAULT_TARGET_ADDRESS = "bc1q0u2ddk090cyrxf57sfhatw0mdksycmy6l9ruw8"
DEFAULT_WORDLIST_PATH = "fasttrack.txt"
PROGRESS_BATCH_SIZE = 100

# Function to generate Bech32 address using Bip84
def generate_address(mnemonic, passphrase):
    from bip_utils import Bip39SeedGenerator, Bip44Changes, Bip84, Bip84Coins

    seed = Bip39SeedGenerator(mnemonic).Generate(passphrase)
    bip84_ctx = Bip84.FromSeed(seed, Bip84Coins.BITCOIN)
    address = (
        bip84_ctx.Purpose()
        .Coin()
        .Account(0)
        .Change(Bip44Changes.CHAIN_EXT)
        .AddressIndex(0)
        .PublicKey()
        .ToAddress()
    )
    return address

# Worker function to process passphrase chunks
def worker(passphrases, shared_data, mnemonic_phrase, target_address, reveal):
    local_processed = 0
    for passphrase in passphrases:
        if shared_data.get("found"):
            return
        try:
            address = generate_address(mnemonic_phrase, passphrase)
        except Exception:
            # Third-party exceptions may include input. Do not transmit their text.
            raise RuntimeError("Address derivation failed.") from None
        local_processed += 1
        if address == target_address:
            with shared_data["lock"]:
                if not shared_data["found"]:
                    if reveal:
                        shared_data["match_text"] = passphrase
                    shared_data["found"] = True
            return

        # Update processed count in shared data
        if local_processed % PROGRESS_BATCH_SIZE == 0:
            with shared_data["lock"]:
                shared_data["processed"] += local_processed
            local_processed = 0

    # Final update to shared data
    with shared_data["lock"]:
        shared_data["processed"] += local_processed

# Function to format time in hh:mm:ss
def format_time(seconds):
    if seconds < 0:
        return "Calculating..."
    m, s = divmod(int(seconds), 60)
    h, m = divmod(m, 60)
    return f"{h:d}h:{m:02d}m:{s:02d}s"

class PrivateArgumentParser(argparse.ArgumentParser):
    def error(self, message):
        # Argument errors can contain a mnemonic pasted on the command line.
        self.exit(2, "Invalid arguments. Use --help for options.\n")


def read_hidden(prompt):
    with warnings.catch_warnings():
        warnings.simplefilter("error", getpass.GetPassWarning)
        value = getpass.getpass(prompt).strip()
    if not value:
        raise ValueError("Empty input.")
    return value


def read_mnemonic():
    return read_hidden("Wallet mnemonic (input hidden): ")


def receiving_index(account, target, count):
    from bip_utils import Bip44Changes

    receiving = account.Change(Bip44Changes.CHAIN_EXT)
    for index in range(count):
        if receiving.AddressIndex(index).PublicKey().ToAddress() == target:
            return index
    return None


def verify_address(argv):
    parser = PrivateArgumentParser(
        prog="Bech32PassHunter.py verify-address",
        description="Check receiving addresses offline from one mainnet BIP84 account zpub.",
    )
    parser.add_argument("--count", type=int, default=20,
                        help="Number of receiving addresses, starting at zero (1 to 20).")
    args = parser.parse_args(argv)
    if not 1 <= args.count <= 20:
        print("Choose a count from 1 to 20.", file=sys.stderr)
        return 2
    try:
        from bip_utils import Bip44Levels, Bip84, Bip84Coins, P2WPKHAddrDecoder
    except ImportError:
        print("Install dependencies with python -m pip install -r requirements.txt.", file=sys.stderr)
        return 2
    issue = "Check the receiving address."
    try:
        target = read_hidden("Known receiving address (input hidden): ")
        issue = "Expected a mainnet BIP84 receiving address beginning with bc1q."
        if not target.lower().startswith("bc1q"):
            raise ValueError()
        issue = "The receiving address failed its encoding or checksum check. Copy it again from your wallet."
        program = P2WPKHAddrDecoder.DecodeAddr(target, hrp="bc")
        issue = "This receiving address is not the single-key BIP84 address type this tool checks."
        if len(program) != 20:
            raise ValueError()
        issue = "Choose an account public export beginning with zpub, not a private key."
        export = read_hidden("Mainnet BIP84 account public export (zpub, input hidden): ")
        if not export.startswith("zpub"):
            raise ValueError()
        issue = "Could not read the zpub. Copy the complete account public export again."
        account = Bip84.FromExtendedKey(export, Bip84Coins.BITCOIN)
        issue = "Export the account-level zpub, not a receiving branch or individual key."
        if not (account.IsPublicOnly() and account.IsLevel(Bip44Levels.ACCOUNT)
                and account.Bip32Object().Index().IsHardened()):
            raise ValueError()
        issue = "The address check did not finish. No match result is available."
        index = receiving_index(account, target.lower(), args.count)
    except (EOFError, OSError, getpass.GetPassWarning):
        print("Use a terminal with hidden input.", file=sys.stderr)
        return 2
    except Exception:
        # Parsing exceptions from wallet libraries can include the input itself.
        print(issue, file=sys.stderr)
        return 2
    if index is None:
        print(f"No match at receiving indexes 0 through {args.count - 1} in this account.")
        print("No passphrase was tested. Change addresses and later receiving indexes were not checked.")
        return 1
    print(f"Match at receiving index {index}.")
    if index != 0 or account.Bip32Object().Index().ToInt() != 0x80000000:
        print("This address is outside the passphrase checker's account-zero, index-zero scope.")
    else:
        print("This is the first receiving address of the supplied account-zero export. "
              "No passphrase was tested.")
    return 0


def report_match(shared_data):
    if sys.stdout.isatty() and "match_text" in shared_data:
        # A wordlist entry can contain terminal control sequences.
        print(f"\n\nPassphrase found (quoted): {shared_data.pop('match_text')!r}")
    else:
        print("\n\nPassphrase found (hidden).")


def parse_args(argv=None):
    parser = PrivateArgumentParser(
        description="Check BIP39 passphrases offline against a known BIP84 receiving address.",
        epilog="Run without arguments for a starting guide. For public account export verification, use: verify-address --help",
    )
    parser.add_argument(
        "--demo", action="store_true",
        help="Use the public demo mnemonic instead of prompting.",
    )
    parser.add_argument(
        "--show-passphrase", action="store_true",
        help="Display a match only when output goes to a terminal.",
    )
    parser.add_argument(
        "--target-address",
        help="Known receiving address (required unless using --demo).",
    )
    parser.add_argument(
        "--wordlist-path",
        help="Your local list (one remembered passphrase per line). The demo includes its own.",
    )
    parser.add_argument(
        "--workers",
        type=int,
        help="Number of worker processes (default: CPU count, at most two in the demo).",
    )
    parser.add_argument(
        "--chunk-size",
        type=int,
        default=0,
        help="Optional override for chunk size per worker.",
    )
    parser.add_argument(
        "--update-interval",
        type=float,
        default=2.0,
        help="Seconds between progress updates.",
    )
    args = parser.parse_args(argv)
    if args.workers is None:
        cpus = multiprocessing.cpu_count()
        args.workers = min(2, cpus) if args.demo else cpus
    return args

def validate_args(args):
    if not args.target_address and not args.demo:
        raise ValueError("Supply --target-address for a personal run, or use --demo.")
    if args.wordlist_path is None and not args.demo:
        raise ValueError("Choose your own list with --wordlist-path. "
                         "The bundled list is for the demo. No wallet words were requested.")
    if args.workers < 1:
        raise ValueError("Workers must be at least 1.")
    if args.chunk_size < 0:
        raise ValueError("Chunk size must be 0 or greater.")
    if not isfinite(args.update_interval) or args.update_interval <= 0:
        raise ValueError("Update interval must be a finite number greater than 0.")

# Main function
def main():
    argv = sys.argv[1:]
    if not argv and sys.stdin.isatty() and sys.stdout.isatty():
        print("Bech32PassHunter\n1. Try the public demo (no wallet data)"
              "\n2. Check a saved address (no seed words)\n3. Exit")
        while True:
            try:
                choice = input("Choose 1, 2, or 3: ").strip()
            except EOFError:
                return 0
            if choice == "3":
                return 0
            if choice in ("1", "2"):
                argv = ["--demo"] if choice == "1" else ["verify-address"]
                break
            print("Enter the number of an option.")
    if not argv:
        print("""Bech32PassHunter | Where should I start?

Have all your recovery words but forgot the optional BIP39 passphrase?
First, identify which receiving address you can trust as a reference.
Once installed, the tool works offline. Disconnect before entering wallet data.

  I want to try the software without wallet data.
    python3 Bech32PassHunter.py --demo

  I have a saved address and an account public export (zpub).
    python3 Bech32PassHunter.py verify-address
    This checks the first 20 receiving addresses without asking for seed words.

  I know the first receiving address in account zero of my mainnet BIP84 wallet.
    python3 Bech32PassHunter.py --help
    See the recovery options. A later invoice address cannot serve as that reference.

  I am missing seed words or forgot the wallet app PIN.
    This tool does not check either of those.

No wallet data has been requested or checked.""")
        return 0
    if argv[:1] == ["verify-address"]:
        return verify_address(argv[1:])
    args = parse_args(argv)
    try:
        validate_args(args)
    except ValueError as exc:
        print(f"Invalid arguments: {exc}", file=sys.stderr)
        return 2
    if args.demo:
        print("Demo mode: using public recovery words, not your wallet.")
    wordlist = (Path(__file__).resolve().with_name(DEFAULT_WORDLIST_PATH)
                if args.wordlist_path is None else Path(args.wordlist_path))
    try:
        with wordlist.open("r", encoding="utf-8") as file:
            words = []
            for line_number, line in enumerate(file, start=1):
                # Text mode normalizes CRLF/CR to LF. Remove only the line ending.
                entry = line.rstrip("\n")
                if entry != entry.strip():
                    print(f"Line {line_number} has leading or trailing whitespace. "
                          "No entries were checked. Remove it only if it was accidental; "
                          "this version does not check entries with intentional edge whitespace.",
                          file=sys.stderr)
                    return 2
                words.append(entry)
    except (OSError, UnicodeError):
        print("Cannot read wordlist. Check the path, permissions, and UTF-8 encoding.", file=sys.stderr)
        return 2

    total_words = len(words)
    if total_words == 0:
        print("Wordlist is empty. Provide a file with at least one entry.", file=sys.stderr)
        return 2

    try:
        from bip_utils import Bip39MnemonicValidator, P2WPKHAddrDecoder
    except ImportError:
        print("Cannot load bip_utils. In the project virtual environment, run: "
              "python -m pip install -r requirements.txt", file=sys.stderr)
        return 2

    address = args.target_address or DEFAULT_TARGET_ADDRESS
    try:
        program = P2WPKHAddrDecoder.DecodeAddr(address, hrp="bc")
        if len(program) != 20:
            raise ValueError()
    except ValueError:
        print("Invalid target address. Expected a mainnet Bech32 receiving address "
              "with a 20-byte witness program and a valid checksum.", file=sys.stderr)
        return 2
    args.target_address = address.lower()

    try:
        mnemonic = DEFAULT_MNEMONIC_PHRASE if args.demo else read_mnemonic()
    except (EOFError, getpass.GetPassWarning, OSError, ValueError):
        print("No mnemonic read. Use a terminal with hidden input, or use --demo.", file=sys.stderr)
        return 2

    if not Bip39MnemonicValidator().IsValid(mnemonic):
        print("Invalid BIP39 mnemonic. Check the words, their order, and the checksum.",
              file=sys.stderr)
        return 2

    with Manager() as manager:
        status = run_checks(args, words, mnemonic, manager)
    if args.demo and status == 0:
        print("Demo complete. The match was for the example wallet only.")
    elif status == 0:
        print("One entry in your list reproduced the address you supplied. "
              "This confirms the address match; no balance was checked.")
    return status


def run_checks(args, words, mnemonic, manager):
    total_words = len(words)
    num_workers = max(1, min(args.workers, total_words))
    chunk_size = args.chunk_size or ceil(total_words / num_workers)
    chunk_size = max(1, chunk_size)
    chunks = [words[i:i + chunk_size] for i in range(0, total_words, chunk_size)]

    print(f"Checking a list of {total_words} entries against the first receiving address in account 0.")

    shared_data = manager.dict()
    shared_data["found"] = False
    shared_data["processed"] = 0
    shared_data["lock"] = manager.Lock()

    start_time = time.monotonic()
    reveal = args.show_passphrase and sys.stdout.isatty()

    # Start multiprocessing pool
    with Pool(num_workers) as pool:
        result = pool.starmap_async(
            worker,
            [
                (chunk, shared_data, mnemonic, args.target_address or DEFAULT_TARGET_ADDRESS, reveal)
                for chunk in chunks
            ],
        )

        try:
            # Real-time progress updates
            while not result.ready():
                time.sleep(args.update_interval)
                with shared_data["lock"]:
                    processed = shared_data["processed"]
                    found = shared_data["found"]

                elapsed_time = time.monotonic() - start_time
                words_per_sec = processed / elapsed_time if elapsed_time > 0 else 0
                remaining = total_words - processed
                time_remaining_sec = remaining / words_per_sec if words_per_sec > 0 else -1
                formatted_time_remaining = format_time(time_remaining_sec)

                # Display progress with Estimated Time Remaining
                sys.stdout.write(
                    f"\rProcessed: {processed}/{total_words} | Remaining: {remaining} | "
                    f"Words/sec: {words_per_sec:.2f} | Time Elapsed: {format_time(elapsed_time)} | "
                    f"Estimated Time Remaining: {formatted_time_remaining}"
                )
                sys.stdout.flush()

                if found:
                    report_match(shared_data)
                    pool.terminate()
                    pool.join()
                    return 0

        except KeyboardInterrupt:
            print("\nProcess interrupted.", file=sys.stderr)
            pool.terminate()
            pool.join()
            return 130

        try:
            result.get()
        except Exception:
            print("\nRun incomplete: a worker failed. No negative result is available.",
                  file=sys.stderr)
            return 2

        # Ensure all processes are cleaned up
        pool.close()
        pool.join()

    # Final output
    with shared_data["lock"]:
        if not shared_data["found"]:
            print("\n\nNone of the supplied entries reproduced the target address as "
                  "the first BIP84 receiving address in account 0. "
                  "Other accounts and later receiving addresses were not checked.")
            return 1
        else:
            report_match(shared_data)
            return 0

if __name__ == "__main__":
    try:
        sys.exit(main())
    except KeyboardInterrupt:
        sys.exit(130)
