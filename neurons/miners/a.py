import pexpect
import sys

cold_wallet_password = 'taominer'
coldkey = "model ill summer divide burger scrub lab neglect found category unveil vendor"
hotkeys = ["cigar mutual phrase stay lake cash gather gentle spray forum gym damp",
           ]
def regenerate_coldkey(seed_phrase, password):
    print("\n--- Regenerating Cold Wallet ---")
    try:
        child = pexpect.spawn('btcli w regen_coldkey', encoding='utf-8')
        child.logfile = sys.stdout  # This will print all output to console

        # Wait for wallet name prompt and automatically enter 'default'
        child.expect('Enter the path for the wallets directory')
        child.sendline("")
        
        child.expect('Enter the name of the new wallet')
        name = input("Enter CK name ") or "default"
        child.sendline(name)

        # Enter mnemonic
        child.expect('Enter the mnemonic, or the seed hex string, or the location of the JSON file.:')
        child.sendline(seed_phrase)

        # Handle potential update warnings
        while True:
            index = child.expect(['Enter your password:', 'Please update to the latest version', pexpect.TIMEOUT, pexpect.EOF], timeout=30)
            if index == 0:
                break
            elif index == 1:
                continue  # Ignore update warning
            else:
                print("Unexpected response or timeout")
                return None

        # Enter password
        child.sendline(password)

        # Confirm password
        child.expect('Retype your password:')
        child.sendline(password)

        # Handle multiple overwrite prompts
        while True:
            index = child.expect(['File .* already exists. Overwrite?', pexpect.EOF], timeout=30)
            if index == 0:
                child.sendline('Y')
            else:
                break  # EOF reached, we're done

        print(f"Coldkey {name} regenerated successfully.")
        return name
    except Exception as e:
        print(f"An error occurred: {str(e)}")
        return None
    finally:
        if 'child' in locals():
            child.close()

def regenerate_hotkey(wallet_name, hotkey_name, seed_phrase):
    print(f"\n--- Regenerating Hot Wallet: {hotkey_name} ---")
    try:
        child = pexpect.spawn('btcli config set --wallet-path ~/.bittensor/wallets/', encoding='utf-8')
        child = pexpect.spawn('btcli w regen_hotkey', encoding='utf-8')
        child.logfile = sys.stdout  # This will print all output to console

        # Enter hotkey name
        child.expect(r".*Enter the ")
        child.sendline('')

        child.expect(r".*Enter the ")
        child.sendline(wallet_name)
        
        child.expect(r".*Enter the ")
        child.sendline(hotkey_name)
        
        # Enter mnemonic
        child.expect('Enter the mnemonic, or the seed hex string, or the location of the JSON file.:')
        child.sendline(seed_phrase)

        # Handle potential overwrite prompt
        while True:
            index = child.expect(['File .* already exists. Overwrite?', pexpect.EOF], timeout=30)
            if index == 0:
                child.sendline('Y')
            else:
                break  # EOF reached, we're done

        print(f"Hotkey '{hotkey_name}' regenerated successfully.")
    except Exception as e:
        print(f"An error occurred: {str(e)}")
    finally:
        if 'child' in locals():
            child.close()

def main():
    print("Starting wallet regeneration process...")

    # Coldkey details
    cold_wallet_seed = coldkey

    # Regenerate cold wallet and get the wallet name
    print("\nRegenerating cold wallet...")
    wallet_name = regenerate_coldkey(cold_wallet_seed, cold_wallet_password)

    if wallet_name:
        # Hot wallet seed phrases
        hot_wallet_seeds = hotkeys

        # Regenerate hot wallets
        print("\nRegenerating hot wallets...")
        for i, seed in enumerate(hot_wallet_seeds, start=1):
            hotkey_name = f"h{i}"
            regenerate_hotkey(wallet_name, hotkey_name, seed)

        print("\nWallet regeneration process completed.")
    else:
        print("\nFailed to regenerate cold wallet. Hot wallet regeneration skipped.")

if __name__ == "__main__":
    main()
