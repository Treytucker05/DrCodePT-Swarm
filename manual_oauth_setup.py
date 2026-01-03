"""
Manual OAuth Setup - Quick workaround to get Google Calendar credentials

Just follow the printed instructions and paste the downloaded credentials.json
"""
import json
from pathlib import Path

def manual_oauth_setup():
    """Guide user through manual OAuth setup."""

    credentials_dir = Path.home() / ".drcodept_swarm" / "google_calendar"
    credentials_path = credentials_dir / "credentials.json"

    print("\n" + "="*70)
    print("  MANUAL GOOGLE CALENDAR OAUTH SETUP")
    print("="*70)
    print("\nSince the automated setup is having issues, let's do this manually.")
    print("It only takes 2 minutes!\n")

    print("STEP 1: Go to Google Cloud Console")
    print("  → https://console.cloud.google.com/apis/credentials")
    print()

    print("STEP 2: Click '+ CREATE CREDENTIALS' → 'OAuth client ID'")
    print()

    print("STEP 3: If prompted, configure the consent screen:")
    print("  - Choose 'External'")
    print("  - Fill in app name (anything, e.g., 'My Calendar App')")
    print("  - Add your email as test user")
    print("  - Click 'Save and Continue' through the steps")
    print()

    print("STEP 4: Create OAuth client ID:")
    print("  - Application type: 'Desktop app'")
    print("  - Name: (anything, e.g., 'Desktop client')")
    print("  - Click 'CREATE'")
    print()

    print("STEP 5: Download the credentials:")
    print("  - Click 'DOWNLOAD JSON' in the popup")
    print("  - Save the file (it will be named something like 'client_secret_XXX.json')")
    print()

    print("="*70)
    print()

    # Get the downloaded file path
    while True:
        file_path = input("Enter the full path to the downloaded JSON file\n(or drag & drop the file here): ").strip().strip('"')

        if not file_path:
            print("Please provide a file path.")
            continue

        file_path = Path(file_path)

        if not file_path.exists():
            print(f"File not found: {file_path}")
            print("Please check the path and try again.")
            continue

        # Verify it's a valid JSON file
        try:
            with open(file_path, 'r') as f:
                data = json.load(f)

            # Check if it has the required OAuth structure
            if "installed" in data or "web" in data:
                # Standard format
                pass
            elif "client_id" in data and "client_secret" in data:
                # Already in the right format
                pass
            else:
                print("\nThis doesn't look like a valid OAuth credentials file.")
                print("It should contain 'client_id' and 'client_secret'.")
                retry = input("Try another file? (y/n): ").strip().lower()
                if retry != 'y':
                    return False
                continue

            # Copy to the right location
            credentials_dir.mkdir(parents=True, exist_ok=True)

            # Copy the file
            with open(file_path, 'r') as src:
                content = src.read()

            with open(credentials_path, 'w') as dst:
                dst.write(content)

            print(f"\n✓ Credentials saved to: {credentials_path}")
            print("\nSetup complete! You can now use Google Calendar features.")
            print("\nTry running: python -m agent.cli 'check my google calendar'")
            return True

        except json.JSONDecodeError:
            print("\nThis file is not valid JSON.")
            retry = input("Try another file? (y/n): ").strip().lower()
            if retry != 'y':
                return False
        except Exception as e:
            print(f"\nError: {e}")
            retry = input("Try another file? (y/n): ").strip().lower()
            if retry != 'y':
                return False

if __name__ == "__main__":
    try:
        success = manual_oauth_setup()
        if success:
            print("\n" + "="*70)
            print("  SUCCESS!")
            print("="*70)
        else:
            print("\nSetup cancelled.")
    except KeyboardInterrupt:
        print("\n\nSetup cancelled.")
    except Exception as e:
        print(f"\n\nError: {e}")
        import traceback
        traceback.print_exc()
