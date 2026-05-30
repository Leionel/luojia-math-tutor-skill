from mineru import MinerU
import sys

client = MinerU()
try:
    result = client.flash_extract(sys.argv[1])
    print("SUCCESS")
    print(result.markdown)
except Exception as e:
    print(f"FAILED: {e}")
