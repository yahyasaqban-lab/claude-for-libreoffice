# Claude for LibreOffice

<p align="center">
  <img src="icons/claude_icon.svg" alt="Claude for LibreOffice" width="120">
</p>

**AI-powered spreadsheet assistance using Claude, directly in LibreOffice Calc.**

A free, open-source alternative to Claude for Excel — no Microsoft required.

## Features

| Feature | Description |
|---------|-------------|
| **Chat Sidebar** | Ask Claude questions about your spreadsheet with full context |
| **Analyze Selection** | Select cells and get instant insights, patterns, and suggestions |
| **Explain Formula** | Understand complex formulas with step-by-step breakdowns |
| **Cell References** | Claude cites specific cells (A1, B2:C5) in its explanations |

### Screenshots

When you open LibreOffice Calc, you'll see a new **Claude** menu:

```
Claude
├── Open Claude Sidebar     (chat interface)
├── Analyze Selection       (insights on selected data)
├── Explain Formula         (formula breakdown)
├── ─────────────────
└── Configure API Key...    (settings)
```

## Installation

### Download Release

1. Download the latest `.oxt` file from [Releases](../../releases)
2. Open LibreOffice Calc
3. Go to **Tools → Extension Manager**
4. Click **Add** and select the downloaded `.oxt` file
5. Restart LibreOffice

### Build from Source

```bash
git clone https://github.com/YOUR_USERNAME/claude-for-libreoffice.git
cd claude-for-libreoffice
./build.sh
unopkg add claude-for-libreoffice-1.0.0.oxt
```

## Configuration

1. Get your API key from [console.anthropic.com](https://console.anthropic.com)
2. In LibreOffice Calc: **Claude → Configure API Key**
3. Enter your key and click Save

Your API key is stored locally at `~/.config/claude-libreoffice/config.json` — never sent anywhere except Anthropic's API.

## Usage

### Chat with Claude

1. **Claude → Open Claude Sidebar**
2. Type your question
3. Check **"Include selected cells"** to send your current selection as context
4. Click **Ask Claude**

Example prompts:
- "What trends do you see in this sales data?"
- "Write a formula to calculate the running total in column C"
- "Why is this VLOOKUP returning #N/A?"

### Analyze Data

1. Select a range of cells
2. **Claude → Analyze Selection**
3. Get insights about patterns, anomalies, and suggestions

### Explain Formulas

1. Select a cell with a formula
2. **Claude → Explain Formula**
3. Get a step-by-step explanation of what it does

## How It Works

```
┌─────────────────────────────────────────────────────────────┐
│  LibreOffice Calc                                           │
│  ┌─────────────────────────────────────────────────────┐   │
│  │  Your Spreadsheet                                    │   │
│  │  ┌───┬───┬───┬───┐                                  │   │
│  │  │ A │ B │ C │ D │  ← Selected cells sent to Claude │   │
│  │  ├───┼───┼───┼───┤                                  │   │
│  │  │   │   │   │   │                                  │   │
│  │  └───┴───┴───┴───┘                                  │   │
│  └─────────────────────────────────────────────────────┘   │
│                           │                                 │
│                           ▼                                 │
│  ┌─────────────────────────────────────────────────────┐   │
│  │  Claude Sidebar                                      │   │
│  │  ┌─────────────────────────────────────────────┐    │   │
│  │  │ Ask: "Explain this formula"                  │    │   │
│  │  └─────────────────────────────────────────────┘    │   │
│  │  [✓] Include selected cells                         │   │
│  │  [Ask Claude]                                       │   │
│  │                                                     │   │
│  │  Response:                                          │   │
│  │  ┌─────────────────────────────────────────────┐    │   │
│  │  │ The formula =SUMIF(A:A,">100",B:B) adds    │    │   │
│  │  │ all values in column B where the           │    │   │
│  │  │ corresponding cell in column A is > 100... │    │   │
│  │  └─────────────────────────────────────────────┘    │   │
│  └─────────────────────────────────────────────────────┘   │
└─────────────────────────────────────────────────────────────┘
                           │
                           ▼ HTTPS
              ┌────────────────────────┐
              │   Anthropic API        │
              │   (Claude claude-sonnet-4-20250514)      │
              └────────────────────────┘
```

## Requirements

- LibreOffice 7.0+ (tested on 25.8)
- **LibreOffice Python scripting support** (see installation below)
- Anthropic API key ([get one here](https://console.anthropic.com))

### Install Python Scripting Support

**Ubuntu/Debian:**
```bash
sudo apt install libreoffice-script-provider-python python3-uno
```

**Fedora:**
```bash
sudo dnf install libreoffice-pyuno
```

**Arch Linux:**
```bash
sudo pacman -S python-uno
```

**macOS (Homebrew):**
```bash
# Python scripting is included in the LibreOffice package
brew install --cask libreoffice
```

**Windows:**
Python scripting is included by default in LibreOffice for Windows.

## Privacy

- Your API key is stored locally only
- Spreadsheet data is sent to Anthropic's API only when you explicitly ask Claude
- No telemetry, no tracking, no data collection

## Roadmap

- [ ] Multi-sheet analysis
- [ ] Create pivot tables via Claude
- [ ] Generate charts from natural language
- [ ] Batch operations on cells
- [ ] LibreOffice Writer support
- [ ] LibreOffice Impress support

## Contributing

PRs welcome! Areas that need work:

1. **Sidebar as true panel** — currently uses a dialog; could use LibreOffice's sidebar panel API
2. **Streaming responses** — show Claude's response as it generates
3. **Keyboard shortcuts** — Ctrl+Shift+C to open sidebar
4. **Better error handling** — more informative error messages

## License

MIT License — use it however you want.

## Acknowledgments

Inspired by [Claude for Excel](https://www.anthropic.com/claude-in-excel) by Anthropic.

---

**Not affiliated with Anthropic.** This is an independent open-source project.
