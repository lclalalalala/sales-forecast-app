#!/usr/bin/env bash
#
# 一键启动前后端开发环境
# ======================
# 用法：./run.sh
#  - 后端：conda dev 环境下启动 Flask (http://localhost:8999)
#  - 前端：npm run dev (http://localhost:5173)
# 按 Ctrl-C 可同时停止前后端。
#

set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
API_DIR="${SCRIPT_DIR}/api"
APP_DIR="${SCRIPT_DIR}/app"
CONDA_BIN="/Users/lucy/miniconda3/condabin/conda"

BACKEND_PID=""

# 清理函数：退出时停止后端
cleanup() {
  if [[ -n "${BACKEND_PID}" ]] && kill -0 "${BACKEND_PID}" 2>/dev/null; then
    echo ""
    echo "正在停止后端服务 (PID: ${BACKEND_PID})..."
    kill "${BACKEND_PID}" 2>/dev/null || true
    wait "${BACKEND_PID}" 2>/dev/null || true
  fi
}
trap cleanup EXIT INT TERM

# 检查依赖
if [[ ! -x "${CONDA_BIN}" ]]; then
  echo "错误：找不到 conda 命令：${CONDA_BIN}"
  exit 1
fi

if [[ ! -d "${API_DIR}" ]]; then
  echo "错误：找不到后端目录：${API_DIR}"
  exit 1
fi

if [[ ! -d "${APP_DIR}" ]]; then
  echo "错误：找不到前端目录：${APP_DIR}"
  exit 1
fi

echo "=============================================="
echo " 启动零售门店库存与需求预测系统"
echo "=============================================="

# 启动后端
echo ""
echo "[1/3] 启动后端 (Flask) ..."
cd "${API_DIR}"
"${CONDA_BIN}" run -n dev python app.py &
BACKEND_PID=$!
cd "${SCRIPT_DIR}"

# 等待后端就绪
echo "[2/3] 等待后端健康检查通过 ..."
for i in {1..30}; do
  if curl -fs "http://localhost:8999/api/health" >/dev/null 2>&1; then
    echo "      后端已就绪：http://localhost:8999"
    break
  fi
  sleep 1
done

if ! curl -fs "http://localhost:8999/api/health" >/dev/null 2>&1; then
  echo "错误：后端未能在 30 秒内启动，请检查 api/app.py 日志"
  exit 1
fi

# 启动前端
echo "[3/3] 启动前端 (Vite) ..."
echo ""
echo "=============================================="
echo " 系统已启动"
echo "   前端：http://localhost:3000"
echo "   后端：http://localhost:8999"
echo "   API： http://localhost:8999/api/overview"
echo "=============================================="
echo ""
cd "${APP_DIR}"
npm run dev
