import time
import sys
import multiprocessing
from multiprocessing import Pool, Manager
from bip_utils import Bip39SeedGenerator, Bip84, Bip84Coins, Bip44Changes
from math import ceil

# Configurations
mnemonic_phrase = "leopard damp effort face charge exclude pilot drum vanish case volume rude warfare call sure embrace drive sure update ugly plastic movie resist pill"
target_address = "bc1q0u2ddk090cyrxf57sfhatw0mdksycmy6l9ruw8"
wordlist_path = "fasttrack.txt"

# Function to generate Bech32 address using Bip84
def generate_address(mnemonic, passphrase):
    seed = Bip39SeedGenerator(mnemonic).Generate(passphrase)
    bip84_ctx = Bip84.FromSeed(seed, Bip84Coins.BITCOIN)
    address = bip84_ctx.Purpose().Coin().Account(0).Change(Bip44Changes.CHAIN_EXT).AddressIndex(0).PublicKey().ToAddress()
    return address

# Worker function to process passphrase chunks
def worker(passphrases, shared_data):
    local_processed = 0
    for passphrase in passphrases:
        passphrase = passphrase.strip()
        try:
            address = generate_address(mnemonic_phrase, passphrase)
            local_processed += 1

            # Check if the address matches the target
            if address == target_address:
                with shared_data["lock"]:
                    shared_data["found"] = passphrase
                return
        except Exception as e:
            # Optionally log the exception
            continue

        # Update processed count in shared data
        if local_processed % 100 == 0:
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

# Main function
def main():
    try:
        with open(wordlist_path, "r", encoding="utf-8", errors="ignore") as file:
            words = file.readlines()
    except FileNotFoundError:
        print("Wordlist file not found. Please check the path.")
        return

    total_words = len(words)
    num_workers = multiprocessing.cpu_count()  # Dynamically set number of workers
    chunk_size = ceil(total_words / num_workers)
    chunks = [words[i:i + chunk_size] for i in range(0, total_words, chunk_size)]

    print(f"Chunks created: {len(chunks)}, Chunk size: {chunk_size}")

    manager = Manager()
    shared_data = manager.dict()
    shared_data["found"] = None
    shared_data["processed"] = 0
    shared_data["lock"] = manager.Lock()

    start_time = time.time()

    # Start multiprocessing pool
    with Pool(num_workers) as pool:
        result = pool.starmap_async(worker, [(chunk, shared_data) for chunk in chunks])

        try:
            # Real-time progress updates
            while not result.ready():
                time.sleep(2)
                with shared_data["lock"]:
                    processed = shared_data["processed"]
                    found = shared_data["found"]

                elapsed_time = time.time() - start_time
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
                    print(f"\n\nPassphrase found: {found}")
                    pool.terminate()
                    pool.join()
                    return

        except KeyboardInterrupt:
            print("\nProcess interrupted by user. Terminating...")
            pool.terminate()
            pool.join()
            return

        # Ensure all processes are cleaned up
        pool.close()
        pool.join()

    # Final output
    with shared_data["lock"]:
        if shared_data["found"] is None:
            print("\n\nPassphrase not found in the given wordlist.")

if __name__ == "__main__":
    main()
