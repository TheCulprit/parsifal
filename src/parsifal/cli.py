import argparse
import sys
import os
from .engine import GrammarParser

def main():
    parser = argparse.ArgumentParser(description="Parsifal: A Dynamic Text Generation Engine")
    
    parser.add_argument("prompt", help="The Parsifal command string to execute")
    parser.add_argument("--dir", "-d", default=".", help="Root directory for templates")
    parser.add_argument("--seed", "-s", type=int, default=None, help="Random seed")
    parser.add_argument("--library", "-l", help="A folder to pre-load using [library]")

    args = parser.parse_args()

    # Use provided seed or generate a random one
    seed = args.seed if args.seed is not None else int.from_bytes(os.urandom(4), "big")

    # Initialize Engine
    p = GrammarParser(root_dir=args.dir, seed=seed)

    # Pre-load library if requested
    if args.library:
        p.load_folder_content(args.library)

    # Parse
    try:
        result = p.parse(args.prompt)
        print(result)
    except Exception as e:
        print(f"Error: {e}", file=sys.stderr)
        sys.exit(1)

if __name__ == "__main__":
    main()