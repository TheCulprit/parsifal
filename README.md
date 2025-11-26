# Parsifal

**A Deterministic, Tag-Based Dynamic Text Generation Engine.**

Parsifal is a Python library built for dynamic text generation—from crafting AI image prompts to generating procedural narratives or RPG content.

It combines simple "Mad Libs" style randomization with a powerful, tag-based registry system for managing complex content libraries.

## 📦 Installation

**Using uv (Recommended):**
```bash
uv add git+https://github.com/TheCulprit/parsifal.git
```

**Using pip:**
```bash
pip install git+https://github.com/TheCulprit/parsifal.git
```

## 🚀 Basic Usage

At its core, Parsifal is a recursive string parser. You can use it for simple randomization, variable storage, and conditional logic.

```python
from parsifal import GrammarParser

# Initialize (Seed ensures reproducibility)
parser = GrammarParser(seed=42)

template = """
[#] 1. Define Variables [/#]
[set name="faction"][ran]Rebels|Empire|Mercenaries[/ran][/set]
[set name="difficulty"][ran]Low|High[/ran][/set]

[#] 2. Generate Mission [/#]
MISSION BRIEFING:
Target: [get var="faction"] Outpost
Objective: [ran]Extract VIP|Sabotage Reactor|Steal Data[/ran]

[#] 3. Conditional Logic [/#]
[if difficulty == High]
    WARNING: Heavy resistance expected. Bring heavy weapons.
[else]
    Intel suggests minimal guard presence. Stealth recommended.
[/else]
"""

print(parser.parse(template))
```

## 📝 Command Syntax

Parsifal uses a unified syntax for all commands.

`[command positional_arg key="value"]`

1.  **Positional Arguments:** Values provided without a name. Order matters.
    *   Example: `[inc score]` ("score" is arg 0).
    *   Example: `[select "outfit, school"]` (The tag string is arg 0).
2.  **Named Arguments:** Values provided as `key="value"`. Order does not matter.
    *   Example: `[loop count="5"]`.
    *   Example: `[select required="outfit" any="school"]`.
3.  **Quotes:** If a value contains spaces or commas, it **must** be wrapped in double `""` or single `''` quotes.
    *   Correct: `[set name="my var"]Value[/set]`
    *   Incorrect: `[set name=my var]Value[/set]` (Parser sees "my" as the name and "var" as a dangling argument).

## 🌟 Feature Highlights

### 1. The Registry System
For larger projects, managing text inside one big string gets messy. Parsifal offers a **Registry System** to decouple your content from your logic. You "register" content into a global pool with tags, and then "select" it based on requirements.

```text
[#] Define your content pool [/#]
[register tags="ship, fighter"]X-Wing[/register]
[register tags="ship, fighter"]TIE Interceptor[/register]
[register tags="ship, capital"]Star Destroyer[/register]

[#] Query the pool [/#]
Patrol encounter: [select required="ship" any="fighter"]
Boss encounter: [select required="ship, capital"]
```

### 2. Contextual Overrides (Intercept & Override)
Parsifal allows you to "hijack" the generation process to force specific outcomes or detail.

*   **`[intercept]`**: Used to replace specific Registry items. If `[select]` picks an item that matches an Intercept's tags, the Intercept runs *instead* of the original item. This allows you to turn a generic result (e.g., "Lava Planet") into a specific named instance (e.g., "Mustafar") without changing your probability tables.
*   **`[override]`**: Used to force variables to a specific value globally, ignoring any `[set]` commands. This is incredibly useful for debugging or creating "Master Control" prompts where you want to lock the generation to a specific theme (e.g., forcing `time_of_day="night"`).

### 3. File System Loading
You don't need to write everything in one file. Parsifal can ingest entire directory trees.

*   **`[library dir="templates"]`**: Recursively loads every `.txt` file in the target folder and adds their contents to the Registry.
*   **`[file name="header.txt"]`**: Inserts the raw content of a specific file at the current position.

### 4. Logic & Probability
Beyond simple randomness, Parsifal offers control flow tools:
*   **`[chance 50]`**: A simple 50% coin flip to render content.
*   **`[loop 5]`**: Repeat generation N times.
*   **`[shuffle]`**: Randomize a list and output *all* items (unlike `[ran]` which picks one).

## 📚 Syntax Reference

### 🎲 Randomization & Lists

#### `[ran]`
Picks one or more items from a list.
*   **Syntax:** `[ran count="1"]Option A|Option B[/ran]`
*   **Arguments:**
    *   `count` (optional): How many items to pick. Default is 1.
*   **Separators:**
    *   Use `|` to separate items on the same line.
    *   **OR** use newlines to separate items.

```text
[ran]Red|Blue|Green[/ran]
[ran]
    Item A
    Item B
[/ran]
```

#### `[shuffle]`
Randomizes a list and returns **all** items.
*   **Syntax:** `[shuffle sep=", "]A|B|C[/shuffle]`

#### `[range]`
Returns a random number within a range.
*   **Syntax:** `[range min="1" max="10"]` OR `[range 1 10]`
*   **Logic:** Returns integer if inputs are integers, float if inputs contain decimals.

#### `[chance]`
A probabilistic coin flip.
*   **Syntax:** `[chance 50]Content[/chance]`

#### `[rw]` & `[irw]`
Appends a random weight to a tag (Common in AI prompting).
*   **Syntax:** `[rw]tag[/rw]` → `(tag:1.24)`
*   **Syntax:** `[irw]tag[/irw]` → `(tag)1.24` (InvokeAI style)

---

### 📂 Registry & Selection

#### `[register]`
Adds content to the global selection pool.
*   **Syntax:** `[register tags="tag1, tag2"]Content[/register]`

#### `[select]`
Picks a random item from the registry based on criteria.
*   **Syntax:** `[select required="a" any="b,c" exclude="d"]`
*   **Arguments:**
    *   `required`: Item **MUST** have ALL of these tags.
    *   `any` (or `oneof`): Item **MUST** have AT LEAST ONE of these tags.
    *   `exclude`: Item **MUST NOT** have any of these tags.

```text
[#] Pick a vehicle that is NOT broken [/#]
[select required="vehicle" exclude="broken"]
```

#### `[intercept]`
Defines a specific override for a selection combination.
*   **Syntax:** `[intercept tags="tag1, tag2"]Content[/intercept]`
*   **Usage:** If `[select]` picks an item containing these tags, run this content instead.

#### `[pass]`
Used inside an `[intercept]` block. Signals the parser to abandon the intercept and run the original content (or the next valid intercept) instead.

---

### 🔧 Variables & Logic

#### `[set]` / `[get]`
Store and retrieve variables.
*   `[set name="color"]Red[/set]`
*   `[get color]`

#### `[inc]` / `[dec]`
Increment or decrement a numeric variable.
*   `[inc score]` / `[dec lives]`

#### `[calc]`
Performs math operations.
*   `[calc]1 + 5 * 2[/calc]`

#### `[if]` / `[elseif]` / `[else]`
Conditional flow.
*   `[if score > 10]...[/if]`
*   `[if my_var == "true"]...[/if]`
*   `[elseif 50%]...[/elseif]` (Can also be used as a probabilistic check).

#### `[switch]`
Pattern matching for variables.
```text
[switch var="status"]
    [case "alert"]Red Alert[/case]
    [case "calm"]All Clear[/case]
    [default]Unknown[/default]
[/switch]
```

#### `[def]` / `[call]`
Define and call reusable macros (functions).
*   `[def name="header"]=== CHAPTER 1 ===[/def]`
*   `[call name="header"]`

---

### 📁 File Operations

*   **`[library dir="path"]`**: Recursively loads all text files in a directory into the Registry.
*   **`[file name="path"]`**: Injects the contents of a specific file.
*   **`[all dir="path"]`**: Injects the contents of *all* files in a directory joined together.

## 💻 Development

This project is managed with `uv`.

1. **Clone the repo:**
   ```bash
   git clone https://github.com/TheCulprit/parsifal.git
   cd parsifal
   ```

2. **Run the CLI (Example):**
   ```bash
   uv run parsifal "[ran]It works!|Hello![/ran]"
   ```

3. **Run Tests:**
   ```bash
   uv run pytest
   ```

## 📄 License

MIT License. See `LICENSE` for details.