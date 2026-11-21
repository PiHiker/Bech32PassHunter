import argparse
import getpass
import multiprocessing
import sys
import time
import warnings
from math import ceil, isfinite
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
        passphrase = passphrase.strip()
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


def read_mnemonic():
    with warnings.catch_warnings():
        warnings.simplefilter("error", getpass.GetPassWarning)
        phrase = getpass.getpass("Wallet mnemonic (input hidden): ").strip()
    if not phrase:
        raise ValueError("No mnemonic entered.")
    return phrase


def report_match(shared_data):
    if sys.stdout.isatty() and "match_text" in shared_data:
        # A wordlist entry can contain terminal control sequences.
        print(f"\n\nPassphrase found (quoted): {shared_data.pop('match_text')!r}")
    else:
        print("\n\nPassphrase found (hidden).")


def parse_args():
    parser = PrivateArgumentParser(
        description="Check BIP39 passphrases against a known BIP84 receiving address."
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
        default=DEFAULT_WORDLIST_PATH,
        help="Path to the wordlist file (one passphrase per line).",
    )
    parser.add_argument(
        "--workers",
        type=int,
        default=multiprocessing.cpu_count(),
        help="Number of worker processes to use (default: CPU count).",
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
    return parser.parse_args()

def validate_args(args):
    if not args.target_address and not args.demo:
        raise ValueError("Supply --target-address for a personal run, or use --demo.")
    if args.workers < 1:
        raise ValueError("Workers must be at least 1.")
    if args.chunk_size < 0:
        raise ValueError("Chunk size must be 0 or greater.")
    if not isfinite(args.update_interval) or args.update_interval <= 0:
        raise ValueError("Update interval must be a finite number greater than 0.")

# Main function
def main():
    args = parse_args()
    try:
        validate_args(args)
    except ValueError as exc:
        print(f"Invalid arguments: {exc}", file=sys.stderr)
        return 2
    try:
        with open(args.wordlist_path, "r", encoding="utf-8") as file:
            words = file.readlines()
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
        return run_checks(args, words, mnemonic, manager)


def run_checks(args, words, mnemonic, manager):
    total_words = len(words)
    num_workers = max(1, min(args.workers, total_words))
    chunk_size = args.chunk_size or ceil(total_words / num_workers)
    chunk_size = max(1, chunk_size)
    chunks = [words[i:i + chunk_size] for i in range(0, total_words, chunk_size)]

    print(f"Chunks created: {len(chunks)}, Chunk size: {chunk_size}")

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
            print("\n\nPassphrase not found in the given wordlist.")
            return 1
        else:
            report_match(shared_data)
            return 0

if __name__ == "__main__":
    try:
        sys.exit(main())
    except KeyboardInterrupt:
        sys.exit(130)
