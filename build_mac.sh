#!/usr/bin/env bash
# ============================================================
# macOS 桌面应用构建脚本
# ------------------------------------------------------------
# 依次：构建前端 → PyInstaller 打包 → 产物在 dist/库存预测系统.app
#
# 前置：
#   conda activate dev
#   pip install -r requirements-desktop.txt
#   (前端) cd app && npm install
# ============================================================
set -euo pipefail

ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
cd "$ROOT"

echo "==> [1/3] 构建前端 (vite build, 使用 .env.production)"
pushd app >/dev/null
npm run build
popd >/dev/null

echo "==> [2/3] 清理旧产物"
rm -rf build dist

echo "==> [3/3] PyInstaller 打包"
pyinstaller desktop.spec --noconfirm

echo ""
echo "✅ 构建完成：$ROOT/dist/库存预测系统.app"
echo "   双击运行，或： open 'dist/库存预测系统.app'"
