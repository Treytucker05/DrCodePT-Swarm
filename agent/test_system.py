from pathlib import Path

OUTPUT = Path("output.txt")
OUTPUT.write_text("Agent Test Successful")
print(OUTPUT.read_text())
OUTPUT.unlink()
