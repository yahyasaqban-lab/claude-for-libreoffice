"""
Claude for LibreOffice Calc - Main Extension Module
Provides AI-powered spreadsheet assistance using Claude API
"""

import uno
from com.sun.star.beans import PropertyValue
from com.sun.star.awt import Rectangle
from com.sun.star.awt.MessageBoxButtons import BUTTONS_OK
from com.sun.star.awt.MessageBoxType import MESSAGEBOX, INFOBOX, WARNINGBOX, ERRORBOX

import os
import json
import sys
from pathlib import Path

# Add bundled packages to path
EXTENSION_DIR = Path(__file__).parent
sys.path.insert(0, str(EXTENSION_DIR / "lib"))

try:
    import anthropic
    ANTHROPIC_AVAILABLE = True
except ImportError:
    ANTHROPIC_AVAILABLE = False

CONFIG_DIR = Path.home() / ".config" / "claude-libreoffice"
CONFIG_FILE = CONFIG_DIR / "config.json"

def get_config():
    """Load configuration from file."""
    if CONFIG_FILE.exists():
        with open(CONFIG_FILE, "r") as f:
            return json.load(f)
    return {}

def save_config(config):
    """Save configuration to file."""
    CONFIG_DIR.mkdir(parents=True, exist_ok=True)
    with open(CONFIG_FILE, "w") as f:
        json.dump(config, f, indent=2)

def get_api_key():
    """Get API key from config or environment."""
    config = get_config()
    return config.get("api_key") or os.environ.get("ANTHROPIC_API_KEY", "")

def get_desktop():
    """Get the LibreOffice desktop."""
    local_context = uno.getComponentContext()
    resolver = local_context.ServiceManager.createInstanceWithContext(
        "com.sun.star.bridge.UnoUrlResolver", local_context
    )
    ctx = local_context
    smgr = ctx.ServiceManager
    desktop = smgr.createInstanceWithContext("com.sun.star.frame.Desktop", ctx)
    return desktop

def get_current_document():
    """Get the current Calc document."""
    desktop = get_desktop()
    return desktop.getCurrentComponent()

def get_current_sheet():
    """Get the active sheet."""
    doc = get_current_document()
    if doc:
        return doc.getSheets().getByIndex(doc.getCurrentController().getActiveSheet().getRangeAddress().Sheet)
    return None

def get_selection_data():
    """Get data from the current selection."""
    doc = get_current_document()
    if not doc:
        return None, None, None

    controller = doc.getCurrentController()
    selection = controller.getSelection()

    if not selection:
        return None, None, None

    # Get selection address
    try:
        addr = selection.getRangeAddress()
        sheet = doc.getSheets().getByIndex(addr.Sheet)
        sheet_name = sheet.getName()

        # Build cell reference string
        start_col = _col_to_letter(addr.StartColumn)
        end_col = _col_to_letter(addr.EndColumn)
        range_str = f"{sheet_name}!{start_col}{addr.StartRow + 1}:{end_col}{addr.EndRow + 1}"

        # Get data array
        data = selection.getDataArray()

        # Get formulas if any
        formulas = selection.getFormulaArray()

        return range_str, data, formulas
    except Exception:
        return None, None, None

def _col_to_letter(col_num):
    """Convert column number to letter(s)."""
    result = ""
    while col_num >= 0:
        result = chr(col_num % 26 + ord('A')) + result
        col_num = col_num // 26 - 1
    return result

def _letter_to_col(letter):
    """Convert column letter(s) to number."""
    result = 0
    for char in letter.upper():
        result = result * 26 + ord(char) - ord('A') + 1
    return result - 1

def show_message(title, message, msg_type=INFOBOX):
    """Show a message box."""
    doc = get_current_document()
    if doc:
        parent_window = doc.getCurrentController().getFrame().getContainerWindow()
        toolkit = parent_window.getToolkit()
        msgbox = toolkit.createMessageBox(
            parent_window, msg_type, BUTTONS_OK, title, message
        )
        msgbox.execute()

def call_claude(prompt, system_prompt=None):
    """Call Claude API with the given prompt."""
    api_key = get_api_key()

    if not api_key:
        return "Error: No API key configured. Please set your API key via Claude > Configure API Key."

    if not ANTHROPIC_AVAILABLE:
        return "Error: Anthropic SDK not installed. Please install it with: pip install anthropic"

    try:
        client = anthropic.Anthropic(api_key=api_key)

        messages = [{"role": "user", "content": prompt}]

        kwargs = {
            "model": "claude-sonnet-4-20250514",
            "max_tokens": 4096,
            "messages": messages,
        }

        if system_prompt:
            kwargs["system"] = system_prompt

        response = client.messages.create(**kwargs)
        return response.content[0].text

    except anthropic.AuthenticationError:
        return "Error: Invalid API key. Please check your API key configuration."
    except anthropic.RateLimitError:
        return "Error: Rate limit exceeded. Please try again later."
    except Exception as e:
        return f"Error calling Claude API: {str(e)}"

def format_data_for_claude(range_str, data, formulas):
    """Format spreadsheet data for Claude."""
    lines = [f"Selected range: {range_str}", ""]

    if data:
        lines.append("Data:")
        for row_idx, row in enumerate(data):
            row_str = " | ".join(str(cell) if cell != "" else "(empty)" for cell in row)
            lines.append(f"  Row {row_idx + 1}: {row_str}")

    if formulas:
        has_formulas = any(cell.startswith("=") for row in formulas for cell in row if cell)
        if has_formulas:
            lines.append("")
            lines.append("Formulas:")
            for row_idx, row in enumerate(formulas):
                for col_idx, formula in enumerate(row):
                    if formula and formula.startswith("="):
                        col_letter = _col_to_letter(col_idx)
                        lines.append(f"  {col_letter}{row_idx + 1}: {formula}")

    return "\n".join(lines)

# ============================================================
# Public functions called from LibreOffice menu/toolbar
# ============================================================

def open_claude_sidebar(*args):
    """Open the Claude sidebar panel."""
    doc = get_current_document()
    if not doc:
        return

    # For now, show a dialog-based chat interface
    # Full sidebar requires more complex panel registration
    _show_chat_dialog()

def _show_chat_dialog():
    """Show the main chat dialog."""
    doc = get_current_document()
    if not doc:
        return

    ctx = uno.getComponentContext()
    smgr = ctx.ServiceManager

    dialog_provider = smgr.createInstanceWithContext(
        "com.sun.star.awt.DialogProvider", ctx
    )

    # Create dialog programmatically
    toolkit = smgr.createInstanceWithContext("com.sun.star.awt.Toolkit", ctx)

    # Get parent window
    frame = doc.getCurrentController().getFrame()
    parent = frame.getContainerWindow()

    # Create dialog
    dialog_model = smgr.createInstanceWithContext(
        "com.sun.star.awt.UnoControlDialogModel", ctx
    )
    dialog_model.Width = 400
    dialog_model.Height = 350
    dialog_model.Title = "Claude for LibreOffice"

    # Add prompt label
    label_model = dialog_model.createInstance(
        "com.sun.star.awt.UnoControlFixedTextModel"
    )
    label_model.Name = "PromptLabel"
    label_model.PositionX = 10
    label_model.PositionY = 10
    label_model.Width = 380
    label_model.Height = 12
    label_model.Label = "Ask Claude about your spreadsheet:"
    dialog_model.insertByName("PromptLabel", label_model)

    # Add input text area
    input_model = dialog_model.createInstance(
        "com.sun.star.awt.UnoControlEditModel"
    )
    input_model.Name = "PromptInput"
    input_model.PositionX = 10
    input_model.PositionY = 25
    input_model.Width = 380
    input_model.Height = 60
    input_model.MultiLine = True
    input_model.VScroll = True
    dialog_model.insertByName("PromptInput", input_model)

    # Add "Include Selection" checkbox
    checkbox_model = dialog_model.createInstance(
        "com.sun.star.awt.UnoControlCheckBoxModel"
    )
    checkbox_model.Name = "IncludeSelection"
    checkbox_model.PositionX = 10
    checkbox_model.PositionY = 90
    checkbox_model.Width = 150
    checkbox_model.Height = 14
    checkbox_model.Label = "Include selected cells"
    checkbox_model.State = 1  # Checked by default
    dialog_model.insertByName("IncludeSelection", checkbox_model)

    # Add Send button
    send_btn_model = dialog_model.createInstance(
        "com.sun.star.awt.UnoControlButtonModel"
    )
    send_btn_model.Name = "SendButton"
    send_btn_model.PositionX = 300
    send_btn_model.PositionY = 88
    send_btn_model.Width = 90
    send_btn_model.Height = 18
    send_btn_model.Label = "Ask Claude"
    dialog_model.insertByName("SendButton", send_btn_model)

    # Add response label
    resp_label_model = dialog_model.createInstance(
        "com.sun.star.awt.UnoControlFixedTextModel"
    )
    resp_label_model.Name = "ResponseLabel"
    resp_label_model.PositionX = 10
    resp_label_model.PositionY = 110
    resp_label_model.Width = 380
    resp_label_model.Height = 12
    resp_label_model.Label = "Claude's response:"
    dialog_model.insertByName("ResponseLabel", resp_label_model)

    # Add response text area
    response_model = dialog_model.createInstance(
        "com.sun.star.awt.UnoControlEditModel"
    )
    response_model.Name = "ResponseOutput"
    response_model.PositionX = 10
    response_model.PositionY = 125
    response_model.Width = 380
    response_model.Height = 180
    response_model.MultiLine = True
    response_model.VScroll = True
    response_model.ReadOnly = True
    dialog_model.insertByName("ResponseOutput", response_model)

    # Add Close button
    close_btn_model = dialog_model.createInstance(
        "com.sun.star.awt.UnoControlButtonModel"
    )
    close_btn_model.Name = "CloseButton"
    close_btn_model.PositionX = 300
    close_btn_model.PositionY = 315
    close_btn_model.Width = 90
    close_btn_model.Height = 18
    close_btn_model.Label = "Close"
    dialog_model.insertByName("CloseButton", close_btn_model)

    # Create dialog control
    dialog = smgr.createInstanceWithContext(
        "com.sun.star.awt.UnoControlDialog", ctx
    )
    dialog.setModel(dialog_model)
    dialog.createPeer(toolkit, parent)

    # Get control references
    send_button = dialog.getControl("SendButton")
    close_button = dialog.getControl("CloseButton")
    prompt_input = dialog.getControl("PromptInput")
    response_output = dialog.getControl("ResponseOutput")
    include_checkbox = dialog.getControl("IncludeSelection")

    # Create action listener for Send button
    class SendButtonListener(unohelper.Base, uno.getTypeByName("com.sun.star.awt.XActionListener")):
        def __init__(self, dialog, prompt_ctrl, response_ctrl, checkbox_ctrl):
            self.dialog = dialog
            self.prompt_ctrl = prompt_ctrl
            self.response_ctrl = response_ctrl
            self.checkbox_ctrl = checkbox_ctrl

        def actionPerformed(self, event):
            prompt = self.prompt_ctrl.getText()
            if not prompt.strip():
                return

            self.response_ctrl.setText("Thinking...")

            # Build full prompt with selection if checked
            full_prompt = prompt
            if self.checkbox_ctrl.getState() == 1:
                range_str, data, formulas = get_selection_data()
                if data:
                    selection_info = format_data_for_claude(range_str, data, formulas)
                    full_prompt = f"{selection_info}\n\nUser question: {prompt}"

            # Call Claude
            system = """You are Claude, an AI assistant integrated into LibreOffice Calc.
You help users analyze spreadsheets, explain formulas, debug errors, and modify data.
When referencing cells, use standard spreadsheet notation (A1, B2:C5, etc.).
When suggesting formulas, use LibreOffice Calc syntax.
Be concise and helpful."""

            response = call_claude(full_prompt, system)
            self.response_ctrl.setText(response)

        def disposing(self, event):
            pass

    # Create action listener for Close button
    class CloseButtonListener(unohelper.Base, uno.getTypeByName("com.sun.star.awt.XActionListener")):
        def __init__(self, dialog):
            self.dialog = dialog

        def actionPerformed(self, event):
            self.dialog.endExecute()

        def disposing(self, event):
            pass

    # We need unohelper for the listeners
    import unohelper

    send_listener = SendButtonListener(dialog, prompt_input, response_output, include_checkbox)
    close_listener = CloseButtonListener(dialog)

    send_button.addActionListener(send_listener)
    close_button.addActionListener(close_listener)

    # Show dialog
    dialog.execute()
    dialog.dispose()

def analyze_selection(*args):
    """Analyze the current selection with Claude."""
    range_str, data, formulas = get_selection_data()

    if not data:
        show_message("Claude", "Please select some cells first.", WARNINGBOX)
        return

    selection_info = format_data_for_claude(range_str, data, formulas)

    prompt = f"""Analyze this spreadsheet selection and provide insights:

{selection_info}

Provide:
1. A summary of what this data represents
2. Any patterns or trends you notice
3. Potential issues or anomalies
4. Suggestions for improvement or additional analysis"""

    system = """You are Claude, an AI assistant analyzing spreadsheet data in LibreOffice Calc.
Provide clear, actionable insights. Reference specific cells when relevant.
Use LibreOffice Calc formula syntax for any suggested formulas."""

    response = call_claude(prompt, system)

    # Show response in a dialog
    _show_response_dialog("Analysis Results", response)

def explain_formula(*args):
    """Explain the formula in the selected cell."""
    range_str, data, formulas = get_selection_data()

    if not formulas:
        show_message("Claude", "Please select a cell with a formula.", WARNINGBOX)
        return

    # Find formulas in selection
    formula_list = []
    for row_idx, row in enumerate(formulas):
        for col_idx, formula in enumerate(row):
            if formula and formula.startswith("="):
                col_letter = _col_to_letter(col_idx)
                formula_list.append(f"{col_letter}{row_idx + 1}: {formula}")

    if not formula_list:
        show_message("Claude", "No formulas found in selection.", WARNINGBOX)
        return

    formulas_text = "\n".join(formula_list)

    prompt = f"""Explain these LibreOffice Calc formulas in detail:

{formulas_text}

For each formula, explain:
1. What it does step by step
2. What each function/operator does
3. What cells/ranges it references
4. The expected result
5. Any potential issues or edge cases"""

    system = """You are Claude, an AI assistant explaining spreadsheet formulas.
Be thorough but clear. Use simple language while being technically accurate.
Reference LibreOffice Calc documentation when relevant."""

    response = call_claude(prompt, system)
    _show_response_dialog("Formula Explanation", response)

def _show_response_dialog(title, response_text):
    """Show a dialog with Claude's response."""
    doc = get_current_document()
    if not doc:
        return

    ctx = uno.getComponentContext()
    smgr = ctx.ServiceManager
    toolkit = smgr.createInstanceWithContext("com.sun.star.awt.Toolkit", ctx)
    frame = doc.getCurrentController().getFrame()
    parent = frame.getContainerWindow()

    dialog_model = smgr.createInstanceWithContext(
        "com.sun.star.awt.UnoControlDialogModel", ctx
    )
    dialog_model.Width = 450
    dialog_model.Height = 350
    dialog_model.Title = title

    # Response text area
    response_model = dialog_model.createInstance(
        "com.sun.star.awt.UnoControlEditModel"
    )
    response_model.Name = "ResponseText"
    response_model.PositionX = 10
    response_model.PositionY = 10
    response_model.Width = 430
    response_model.Height = 300
    response_model.MultiLine = True
    response_model.VScroll = True
    response_model.ReadOnly = True
    response_model.Text = response_text
    dialog_model.insertByName("ResponseText", response_model)

    # Close button
    close_btn_model = dialog_model.createInstance(
        "com.sun.star.awt.UnoControlButtonModel"
    )
    close_btn_model.Name = "CloseButton"
    close_btn_model.PositionX = 350
    close_btn_model.PositionY = 320
    close_btn_model.Width = 90
    close_btn_model.Height = 18
    close_btn_model.Label = "Close"
    close_btn_model.PushButtonType = 2  # CANCEL - closes dialog
    dialog_model.insertByName("CloseButton", close_btn_model)

    dialog = smgr.createInstanceWithContext(
        "com.sun.star.awt.UnoControlDialog", ctx
    )
    dialog.setModel(dialog_model)
    dialog.createPeer(toolkit, parent)
    dialog.execute()
    dialog.dispose()

def configure_api_key(*args):
    """Configure the Claude API key."""
    doc = get_current_document()
    if not doc:
        return

    ctx = uno.getComponentContext()
    smgr = ctx.ServiceManager
    toolkit = smgr.createInstanceWithContext("com.sun.star.awt.Toolkit", ctx)
    frame = doc.getCurrentController().getFrame()
    parent = frame.getContainerWindow()

    dialog_model = smgr.createInstanceWithContext(
        "com.sun.star.awt.UnoControlDialogModel", ctx
    )
    dialog_model.Width = 350
    dialog_model.Height = 120
    dialog_model.Title = "Configure Claude API Key"

    # Label
    label_model = dialog_model.createInstance(
        "com.sun.star.awt.UnoControlFixedTextModel"
    )
    label_model.Name = "Label"
    label_model.PositionX = 10
    label_model.PositionY = 10
    label_model.Width = 330
    label_model.Height = 12
    label_model.Label = "Enter your Anthropic API key:"
    dialog_model.insertByName("Label", label_model)

    # API key input
    input_model = dialog_model.createInstance(
        "com.sun.star.awt.UnoControlEditModel"
    )
    input_model.Name = "ApiKeyInput"
    input_model.PositionX = 10
    input_model.PositionY = 25
    input_model.Width = 330
    input_model.Height = 20
    input_model.EchoChar = ord('*')  # Mask input
    input_model.Text = get_api_key()
    dialog_model.insertByName("ApiKeyInput", input_model)

    # Info label
    info_model = dialog_model.createInstance(
        "com.sun.star.awt.UnoControlFixedTextModel"
    )
    info_model.Name = "InfoLabel"
    info_model.PositionX = 10
    info_model.PositionY = 50
    info_model.Width = 330
    info_model.Height = 24
    info_model.Label = "Get your API key at https://console.anthropic.com\nYour key is stored locally in ~/.config/claude-libreoffice/"
    info_model.MultiLine = True
    dialog_model.insertByName("InfoLabel", info_model)

    # Save button
    save_btn_model = dialog_model.createInstance(
        "com.sun.star.awt.UnoControlButtonModel"
    )
    save_btn_model.Name = "SaveButton"
    save_btn_model.PositionX = 170
    save_btn_model.PositionY = 90
    save_btn_model.Width = 80
    save_btn_model.Height = 18
    save_btn_model.Label = "Save"
    save_btn_model.PushButtonType = 1  # OK
    dialog_model.insertByName("SaveButton", save_btn_model)

    # Cancel button
    cancel_btn_model = dialog_model.createInstance(
        "com.sun.star.awt.UnoControlButtonModel"
    )
    cancel_btn_model.Name = "CancelButton"
    cancel_btn_model.PositionX = 260
    cancel_btn_model.PositionY = 90
    cancel_btn_model.Width = 80
    cancel_btn_model.Height = 18
    cancel_btn_model.Label = "Cancel"
    cancel_btn_model.PushButtonType = 2  # CANCEL
    dialog_model.insertByName("CancelButton", cancel_btn_model)

    dialog = smgr.createInstanceWithContext(
        "com.sun.star.awt.UnoControlDialog", ctx
    )
    dialog.setModel(dialog_model)
    dialog.createPeer(toolkit, parent)

    result = dialog.execute()

    if result == 1:  # OK pressed
        api_key_input = dialog.getControl("ApiKeyInput")
        new_key = api_key_input.getText().strip()
        if new_key:
            config = get_config()
            config["api_key"] = new_key
            save_config(config)
            show_message("Claude", "API key saved successfully!", INFOBOX)

    dialog.dispose()

# Additional utility functions for advanced operations

def write_to_cells(start_cell, data):
    """Write data to cells starting from start_cell.

    Args:
        start_cell: String like "A1" or "Sheet1.B2"
        data: 2D list of values to write
    """
    doc = get_current_document()
    if not doc:
        return False

    try:
        sheet = doc.getSheets().getByIndex(0)

        # Parse cell reference
        if "." in start_cell:
            sheet_name, cell_ref = start_cell.split(".", 1)
            sheet = doc.getSheets().getByName(sheet_name)
        else:
            cell_ref = start_cell

        # Parse column and row
        col_str = ""
        row_str = ""
        for char in cell_ref:
            if char.isalpha():
                col_str += char
            else:
                row_str += char

        start_col = _letter_to_col(col_str)
        start_row = int(row_str) - 1

        # Get range and set data
        num_rows = len(data)
        num_cols = len(data[0]) if data else 0

        cell_range = sheet.getCellRangeByPosition(
            start_col, start_row,
            start_col + num_cols - 1, start_row + num_rows - 1
        )
        cell_range.setDataArray(data)
        return True

    except Exception as e:
        show_message("Claude", f"Error writing to cells: {e}", ERRORBOX)
        return False

def get_sheet_summary():
    """Get a summary of all sheets in the document."""
    doc = get_current_document()
    if not doc:
        return None

    summary = []
    sheets = doc.getSheets()

    for i in range(sheets.getCount()):
        sheet = sheets.getByIndex(i)
        name = sheet.getName()

        # Get used range
        cursor = sheet.createCursor()
        cursor.gotoEndOfUsedArea(True)
        cursor.gotoStartOfUsedArea(True)

        addr = cursor.getRangeAddress()
        used_range = f"{_col_to_letter(addr.StartColumn)}{addr.StartRow + 1}:{_col_to_letter(addr.EndColumn)}{addr.EndRow + 1}"

        summary.append({
            "name": name,
            "index": i,
            "used_range": used_range,
            "rows": addr.EndRow - addr.StartRow + 1,
            "cols": addr.EndColumn - addr.StartColumn + 1
        })

    return summary

# Register as UNO component
g_exportedScripts = (
    open_claude_sidebar,
    analyze_selection,
    explain_formula,
    configure_api_key,
)
