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

# 启用作业控制：每个后台任务拥有独立的进程组，
# 这样退出时可以向整个进程组发送信号（连同 conda run / npm 派生的子进程一起结束）。
set -m

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
API_DIR="${SCRIPT_DIR}/api"
APP_DIR="${SCRIPT_DIR}/app"
CONDA_BIN="/Users/lucy/miniconda3/condabin/conda"

BACKEND_PORT=8999
FRONTEND_PORT=3000

BACKEND_PID=""
FRONTEND_PID=""

# 释放端口：若端口被占用，强制结束占用它的进程。
free_port() {
  local port="$1" name="$2"
  local pids
  # -ti 仅输出监听该端口的进程 PID（可能多个）
  pids="$(lsof -ti "tcp:${port}" -sTCP:LISTEN 2>/dev/null || true)"
  [[ -n "${pids}" ]] || return 0

  echo "端口 ${port}（${name}）已被占用，正在强制释放：PID ${pids//$'\n'/ }"
  # 先 TERM 优雅退出
  kill -TERM ${pids} 2>/dev/null || true
  for _ in {1..10}; do
    pids="$(lsof -ti "tcp:${port}" -sTCP:LISTEN 2>/dev/null || true)"
    [[ -n "${pids}" ]] || { echo "      端口 ${port} 已释放。"; return 0; }
    sleep 0.5
  done

  # 仍占用则强杀
  echo "      端口 ${port} 未能优雅释放，强制结束 ..."
  kill -KILL ${pids} 2>/dev/null || true
  sleep 0.5
  if lsof -ti "tcp:${port}" -sTCP:LISTEN >/dev/null 2>&1; then
    echo "错误：无法释放端口 ${port}，请手动检查。"
    exit 1
  fi
  echo "      端口 ${port} 已释放。"
}

# 优雅停止一个进程组：先发送 TERM，等待若干秒后仍存活则发送 KILL。
stop_pgid() {
  local pid="$1" name="$2"
  [[ -n "${pid}" ]] || return 0
  kill -0 "${pid}" 2>/dev/null || return 0

  echo "正在停止${name} (PID: ${pid})..."
  # 负号表示向整个进程组发送信号（覆盖 conda run / npm 派生的子进程）。
  kill -TERM "-${pid}" 2>/dev/null || kill -TERM "${pid}" 2>/dev/null || true

  # 最多等待 10 秒优雅退出
  for _ in {1..20}; do
    kill -0 "${pid}" 2>/dev/null || return 0
    sleep 0.5
  done

  echo "${name}未在超时时间内退出，强制结束 ..."
  kill -KILL "-${pid}" 2>/dev/null || kill -KILL "${pid}" 2>/dev/null || true
  wait "${pid}" 2>/dev/null || true
}

# 清理函数：退出时同时停止前端和后端
cleanup() {
  # 解除 trap，避免清理过程中重复触发
  trap - EXIT INT TERM
  echo ""
  echo "正在关闭服务 ..."
  stop_pgid "${FRONTEND_PID}" "前端服务"
  stop_pgid "${BACKEND_PID}" "后端服务"
  echo "已全部停止。"
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
free_port "${BACKEND_PORT}" "后端"
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
free_port "${FRONTEND_PORT}" "前端"
echo ""
echo "=============================================="
echo " 系统已启动"
echo "   前端：http://localhost:3000"
echo "   后端：http://localhost:8999"
echo "   API： http://localhost:8999/api/overview"
echo "=============================================="
echo ""
cd "${APP_DIR}"
npm run dev &
FRONTEND_PID=$!
cd "${SCRIPT_DIR}"

# 前台等待前端进程；收到 Ctrl-C 时 wait 被中断，触发 cleanup 同时停止前后端。
wait "${FRONTEND_PID}"
