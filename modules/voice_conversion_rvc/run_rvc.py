import argparse
import shutil
import sys
from pathlib import Path

def main():
    parser = argparse.ArgumentParser(description="RVC Stub Script")
    parser.add_argument("--model", help="Path to model checkpoint")
    parser.add_argument("--source", required=True, help="Input audio path")
    parser.add_argument("--output", required=True, help="Output audio path")
    parser.add_argument("--f0", help="f0 method")
    parser.add_argument("--hop-length", help="hop length")
    parser.add_argument("--filter-radius", help="filter radius")
    parser.add_argument("--spk-id", help="speaker id")
    parser.add_argument("--index", help="index path")
    parser.add_argument("--pitch", help="pitch shift")
    
    args = parser.parse_args()
    
    input_path = Path(args.source)
    output_path = Path(args.output)
    
    if not input_path.exists():
        print(f"Error: Input file not found: {input_path}")
        sys.exit(1)
        
    print(f"RVC Stub: Copying {input_path} to {output_path}")
    shutil.copy2(input_path, output_path)
    print("RVC Stub: Done.")

if __name__ == "__main__":
    main()
