import os
import re
import pytest
from .engine import GrammarParser

# --- Colors ---
GREEN = "\033[92m"
RED = "\033[91m"
RESET = "\033[0m"

# --- Verbose Helper ---

def check(parser, input_text, expected, desc, regex=False, validator=None):
    """
    Runs a test case with verbose logging.
    
    Args:
        input_text: The raw string to parse.
        expected: The expected output string (or description if using validator).
        desc: Brief description of the test.
        regex: If True, 'expected' is treated as a regex pattern.
        validator: Optional function(result) -> bool for complex checks.
    """
    print(f"\n{'-'*80}")
    print(f"[TEST] {desc}")
    print(f"  Input:    {repr(input_text)}")
    
    # Execute
    try:
        result = parser.parse(input_text)
        print(f"  Result:   {repr(result)}")
        
        # Determine Pass/Fail
        passed = False
        if validator:
            passed = validator(result)
            print(f"  Expected: (Validator) {expected}")
        elif regex:
            passed = bool(re.match(expected, result))
            print(f"  Pattern:  {repr(expected)}")
        else:
            passed = (result == expected)
            print(f"  Expected: {repr(expected)}")
            
        # Print Status
        if passed:
            print(f"  Status:   {GREEN}PASSED{RESET}")
        else:
            print(f"  Status:   {RED}FAILED{RESET}")
            
        # Assertion (Triggers Pytest Failure)
        if validator:
            assert passed, f"Validator failed for result '{result}'. Expected: {expected}"
        elif regex:
            assert re.match(expected, result), f"Result '{result}' did not match pattern '{expected}'"
        else:
            assert result == expected, f"Expected '{expected}', got '{result}'"

    except Exception as e:
        print(f"  Status:   {RED}CRASH{RESET}")
        print(f"  Error:    {e}")
        raise e

# --- Fixtures ---

@pytest.fixture
def parser(tmp_path):
    """
    Initializes parser with a temp file structure for file/library tests.
    Seed 42 is used for determinism.
    """
    # Create Root Dir
    root = tmp_path / "data"
    root.mkdir()
    
    # Create single file
    (root / "hello.txt").write_text("Hello World", encoding="utf-8")
    
    # Create subdirectory 'notes'
    notes = root / "notes"
    notes.mkdir()
    (notes / "a.txt").write_text("Alpha", encoding="utf-8")
    (notes / "b.txt").write_text("Beta", encoding="utf-8")
    
    # Create library definition file
    lib = root / "defs"
    lib.mkdir()
    (lib / "colors.txt").write_text("[register tags=color]Red[/register]\n[register tags=color]Blue[/register]", encoding="utf-8")

    # Initialize Parser
    p = GrammarParser(root_dir=str(root), seed=42)
    return p

# --- 1. Variables ---

def test_variables(parser):
    print("\n=== CATEGORY: Variables ===")
    
    # 1. [set]
    check(parser, 
          "[set name=hero]Parsifal[/set][get hero]", 
          "Parsifal", 
          "Set/Get: Named Argument")
    
    check(parser, 
          "[set count]10[/set][get count]", 
          "10", 
          "Set/Get: Positional Argument")
          
    check(parser,
          "[set nested][set inner]Val[/set][get inner][/set][get nested]",
          "Val",
          "Set: Nested tag resolution")

    # 2. [override]
    check(parser, 
          "[override name=hero]Galahad[/override][get hero]", 
          "Galahad", 
          "Override: Named Argument")
          
    check(parser, 
          "[override hero]Lancelot[/override][get hero]", 
          "Lancelot", 
          "Override: Positional Argument")

    # 3. [inc]
    check(parser, "[set i]5[/set][inc i][get i]", "6", "Inc: Existing Variable")
    check(parser, "[inc new_var][get new_var]", "1", "Inc: Missing Variable (Defaults 0->1)")

    # 4. [dec]
    check(parser, "[set d]10[/set][dec d][get d]", "9", "Dec: Existing Variable")
    check(parser, "[dec missing][get missing]", "-1", "Dec: Missing Variable (Defaults 0->-1)")

    # 5. [exists]
    check(parser, "[set found]1[/set][exists found]", "1", "Exists: True")
    check(parser, "[exists not_found]", "", "Exists: False")

# --- 2. Logic ---

def test_logic(parser):
    print("\n=== CATEGORY: Logic ===")
    parser.parse("[set a]1[/set][set b]2[/set]")

    # 1. [if]
    check(parser, "[if a==1]Yes[/if]", "Yes", "If: Equality True")
    check(parser, "[if a!=1]Yes[/if]", "", "If: Inequality False")
    check(parser, "[if a==1][if b==2]Both[/if][/if]", "Both", "If: Nested")

    # 2. [else]
    check(parser, "[if a==99]No[/if][else]Yes[/else]", "Yes", "Else: Fallback")
    check(parser, "[if a==1]Yes[/if][else]No[/else]", "Yes", "Else: Skipped if prev true")

    # 3. [elseif]
    template = "[if a==99]No[/if][elseif a==1]Yes[/elseif][else]Fallback[/else]"
    check(parser, template, "Yes", "ElseIf: Triggered")
    
    template_skip = "[if a==1]First[/if][elseif a==1]Second[/elseif]"
    check(parser, template_skip, "First", "ElseIf: Skipped if prev true")

    # 4. [switch]
    check(parser, 
          "[switch a][case 1]One[/case][case 2]Two[/case][/switch]", 
          "One", 
          "Switch: Case Match")
          
    check(parser, 
          "[switch b][case 1]One[/case][default]Def[/default][/switch]", 
          "Def", 
          "Switch: Default Match")

# --- 3. Math ---

def test_math(parser):
    print("\n=== CATEGORY: Math ===")

    # 1. [calc]
    check(parser, "[calc]5 + 5[/calc]", "10", "Calc: Addition")
    check(parser, "[calc]max(10, 20)[/calc]", "20", "Calc: Built-in Math Functions")
    
    parser.parse("[set n]5[/set]")
    check(parser, "[calc][get n] * 2[/calc]", "10", "Calc: With Variables")

    # 2. [range]
    check(parser, "[range 10 10]", "10", "Range: Exact Int (Positional)")
    check(parser, "[range min=5 max=5]", "5", "Range: Exact Int (Named)")
    check(parser, "[range 0.5 0.5]", "0.500", "Range: Exact Float")

    # 3. [len]
    check(parser, "[len]ABC[/len]", "3", "Len: String")
    check(parser, "[len][/len]", "0", "Len: Empty")

# --- 4. Loops & Control ---

def test_loops_control(parser):
    print("\n=== CATEGORY: Loops & Control ===")

    # 1. [loop]
    check(parser, "[loop count=2]X[/loop]", "XX", "Loop: Named Count")
    check(parser, "[loop 2]Y[/loop]", "YY", "Loop: Positional Count")

    # 2. [break]
    check(parser, 
          "[loop 5]A[break]B[/loop]", 
          "A", 
          "Break: Immediate")
          
    parser.parse("[set stop_at]3[/set][set i]0[/set]")
    # Loop 5 times. Inc i. If i==3 break.
    check(parser, 
          "[loop 5][inc i][get i][if i==3][break][/if][/loop]", 
          "123", 
          "Break: Conditional")

    # 3. [stop]
    check(parser, "Start [stop] End", "Start", "Stop: Halts Execution")

# --- 5. Random ---

def test_random(parser):
    print("\n=== CATEGORY: Random ===")

    # 1. [ran]
    check(parser, "[ran]A|B|C[/ran]", "C", "Ran: Pipe Separated") # Seed 42 -> C
    
    # Seed 42 for ['A','B','C'] k=2 -> ['A', 'C']. 
    check(parser, "[ran count=2]A|B|C[/ran]", "A, C", "Ran: Multiple Picks")
    
    # 2. [ran] with Newlines
    check(parser, "[ran]\nA\nB\nC\n[/ran]", "C", "Ran: Newline Separated")

    # 3. [chance]
    check(parser, "[chance 100]Yes[/chance]", "Yes", "Chance: 100%")
    check(parser, "[chance 0]Yes[/chance]", "", "Chance: 0%")

    # 4. [shuffle]
    def validate_shuffle(res):
        return len(res) == 5 and "A" in res and "B" in res and "|" in res
        
    check(parser, 
          "[shuffle]A|B|C[/shuffle]", 
          "String containing A, B, C and separators", 
          "Shuffle: List", 
          validator=validate_shuffle)

    # 5. [join]
    check(parser, "[join sep=-]A|B|C[/join]", "A-B-C", "Join: Custom Separator")

    # 6. NESTED RAN (Known Failure)
    check(parser, 
          "[ran][ran]1|2[/ran]|[ran]3|4[/ran][/ran]", 
          "2", 
          "Ran: Nested Pipes (KNOWN FAIL)")

# --- 6. Weighting ---

def test_weighting(parser):
    print("\n=== CATEGORY: Weighting ===")

    # 1. [rw]
    check(parser, 
          "[rw]Tag[/rw]", 
          r"^\(Tag:1\.\d{3}\)$", 
          "RW: Standard Default", 
          regex=True)
          
    check(parser, 
          "[rw 5.0 5.0]Tag[/rw]", 
          "(Tag:5.000)", 
          "RW: Explicit Range")

    # 2. [irw]
    check(parser, 
          "[irw]Tag[/irw]", 
          r"^\(Tag\)1\.\d{3}$", 
          "IRW: Standard Default", 
          regex=True)
          
    check(parser, 
          "[irw 2.5 2.5]Tag[/irw]", 
          "(Tag)2.500", 
          "IRW: Explicit Range")

# --- 7. Files & Library ---

def test_filesystem(parser):
    print("\n=== CATEGORY: Filesystem ===")

    # 1. [file]
    check(parser, "[file name=hello.txt]", "Hello World", "File: Read existing")
    check(parser, "[file missing.txt]", "", "File: Read missing (empty)")

    # 2. [all]
    # Reads 'notes' dir containing a.txt (Alpha) and b.txt (Beta)
    check(parser, "[all dir=notes]", "Alpha\nBeta", "All: Read Directory")

    # 3. [library]
    parser.parse("[library dir=defs]")
    
    # Verify by checking [select]
    def validate_lib(res):
        return res in ["Red", "Blue"]
        
    check(parser, 
          "[select color]", 
          "Red or Blue", 
          "Library: Load and Verify Selection",
          validator=validate_lib)

# --- 8. Registry System ---

def test_registry(parser):
    print("\n=== CATEGORY: Registry ===")

    # 1. [register]
    # UPDATED: Changed tags= to required=
    parser.parse("[register tags=t1,item1]Item1[/register]")
    parser.parse("[register tags=t1,item2]Item2[/register]")
    
    # 2. [select]
    def validate_select(res):
        return res in ["Item1", "Item2"]
        
    check(parser, "[select t1]", "Item1 or Item2", "Select: Basic", validator=validate_select)
    
    # 3. [select] with exclusion
    # We exclude tag 'item1', so only Item2 should remain.
    check(parser, "[select tags=t1 exclude=item1]", "Item2", "Select: Exclusion")

    # 4. [intercept]
    # NOTE: Intercept still uses tags= logic in the engine
    parser.parse("[intercept tags=t1]Intercepted[/intercept]")
    check(parser, "[select t1]", "Intercepted", "Intercept: Trigger")

    # 5. [pass]
    parser = GrammarParser(root_dir=".", seed=42)
    # UPDATED: Changed tags= to required=
    parser.parse("[register tags=test]Original[/register]")
    parser.parse("[intercept tags=test]Filtered [pass][/intercept]")
    
    check(parser, "[select test]", "Original", "Pass: Skips Intercept")

# --- 9. Macros ---

def test_macros(parser):
    print("\n=== CATEGORY: Macros ===")

    # 1. [def]
    parser.parse("[def name=greet]Hello [get x][/def]")
    parser.parse("[set x]World[/set]")

    # 2. [call]
    check(parser, "[call greet]", "Hello World", "Macro: Call with State")
    check(parser, "[call missing]", "", "Macro: Call Missing")

# --- 10. Meta & Comments ---

def test_meta(parser):
    print("\n=== CATEGORY: Meta ===")

    # 1. [mute]
    check(parser, "[mute]Hidden [set x]1[/set][/mute][get x]", "1", "Mute: Hides output, runs logic")

    # 2. [ignore]
    check(parser, "[ignore][if][/ignore]", "[if]", "Ignore: Raw Output")

    # 3. Comments
    check(parser, "A[#]Hash[/#]B", "AB", "Comment: Hash")
    check(parser, "A[comment]Block[/comment]B", "AB", "Comment: Block")