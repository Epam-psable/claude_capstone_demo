#!/bin/sh
# Install git hooks for the SDLC pipeline

HOOKS_DIR=".git/hooks"
SRC_DIR="scripts/hooks"

if [ ! -d "$HOOKS_DIR" ]; then
    echo "ERROR: .git/hooks not found — run this from the repo root"
    exit 1
fi

cp "$SRC_DIR/pre-commit"  "$HOOKS_DIR/pre-commit"
cp "$SRC_DIR/post-commit" "$HOOKS_DIR/post-commit"
chmod +x "$HOOKS_DIR/pre-commit" "$HOOKS_DIR/post-commit"

echo "Git hooks installed:"
echo "  .git/hooks/pre-commit  — validates SDLC artifacts, blocks committed secrets"
echo "  .git/hooks/post-commit — logs commits, suggests next pipeline stage"
