#!/bin/bash
# Build script for Claude for LibreOffice extension

set -e

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
cd "$SCRIPT_DIR"

VERSION="1.0.0"
OUTPUT_NAME="claude-for-libreoffice-${VERSION}.oxt"

echo "Building Claude for LibreOffice extension..."

# Create lib directory and install anthropic SDK
echo "Bundling anthropic SDK..."
mkdir -p python/lib
pip install --target=python/lib --upgrade anthropic httpx 2>/dev/null || {
    echo "Warning: Could not bundle anthropic SDK."
    echo "Users will need to install it manually: pip install anthropic"
}

# Remove unnecessary files from bundled packages
find python/lib -name "*.pyc" -delete 2>/dev/null || true
find python/lib -name "__pycache__" -type d -exec rm -rf {} + 2>/dev/null || true
find python/lib -name "*.dist-info" -type d -exec rm -rf {} + 2>/dev/null || true
find python/lib -name "tests" -type d -exec rm -rf {} + 2>/dev/null || true

# Remove old build
rm -f "$OUTPUT_NAME"

# Create the .oxt file (it's just a ZIP)
echo "Creating extension package..."
zip -r "$OUTPUT_NAME" \
    META-INF/ \
    python/ \
    dialogs/ \
    icons/ \
    description/ \
    description.xml \
    Addons.xcu \
    OptionsDialog.xcu \
    -x "*.pyc" \
    -x "*__pycache__*" \
    -x "*.svg"

echo ""
echo "Build complete: $OUTPUT_NAME"
echo ""
echo "To install:"
echo "  1. Open LibreOffice Calc"
echo "  2. Go to Tools > Extension Manager"
echo "  3. Click 'Add' and select $OUTPUT_NAME"
echo "  4. Restart LibreOffice"
echo ""
echo "Or install via command line:"
echo "  unopkg add --shared $OUTPUT_NAME"
echo ""
