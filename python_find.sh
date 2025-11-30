#!/usr/bin/env bash
set -e

# ---- CONFIG ----
SDK_ROOT="$HOME/android-sdk"
NDK_VERSION="28.2.13676358"
NDK_DIR="$SDK_ROOT/ndk/$NDK_VERSION"
PYTHON_INCLUDE_DIR="$NDK_DIR/toolchains/llvm/prebuilt/linux-x86_64/python3/include"

# ---- COLORS ----
GREEN="\033[0;32m"
RED="\033[0;31m"
NC="\033[0m"

echo -e "${GREEN}[INFO] Checking Android SDK root at:${NC} $SDK_ROOT"

# ---- Ensure sdkmanager exists ----
if [ ! -f "$SDK_ROOT/cmdline-tools/latest/bin/sdkmanager" ]; then
  echo -e "${RED}[WARN] sdkmanager not found. Installing...${NC}"
  mkdir -p "$SDK_ROOT/cmdline-tools/latest"
  cd "$SDK_ROOT/cmdline-tools/latest"
  curl -sSL https://dl.google.com/android/repository/commandlinetools-linux-13114758_latest.zip -o tools.zip
  unzip -q tools.zip
  rm tools.zip

  # Some zips create nested "cmdline-tools" folder, fix path if needed
  if [ -d "$SDK_ROOT/cmdline-tools/latest/cmdline-tools" ]; then
    mv "$SDK_ROOT/cmdline-tools/latest/cmdline-tools/"* "$SDK_ROOT/cmdline-tools/latest/"
    rm -rf "$SDK_ROOT/cmdline-tools/latest/cmdline-tools"
  fi
fi

SDKMANAGER="$SDK_ROOT/cmdline-tools/latest/bin/sdkmanager"

# ---- Install NDK if missing ----
if [ ! -d "$NDK_DIR" ]; then
  echo -e "${GREEN}[INFO] Installing NDK version $NDK_VERSION...${NC}"
  yes | "$SDKMANAGER" --sdk_root="$SDK_ROOT" "ndk;$NDK_VERSION"
else
  echo -e "${GREEN}[OK] NDK already installed at:${NC} $NDK_DIR"
fi

# ---- Check Python include path ----
if [ -d "$PYTHON_INCLUDE_DIR" ]; then
  echo -e "${GREEN}[FOUND] python3 include directory:${NC} $PYTHON_INCLUDE_DIR"
  ls -la "$PYTHON_INCLUDE_DIR"
else
  echo -e "${RED}[MISSING] python3 include directory not found!${NC}"
  echo "Expected path: $PYTHON_INCLUDE_DIR"
fi
