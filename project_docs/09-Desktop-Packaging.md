# 09 - 桌面应用打包指南

将前端（`app`）与后端（`api`）连同数据、配置打包为 **macOS / Windows 原生桌面应用**，双击即用，终端用户无需安装 Python、Node 或浏览器。

## 1. 架构

```
┌──────────────────────────────────────────────┐
│  可执行程序（库存预测系统.app / .exe）           │
│                                               │
│  desktop.py（入口）                            │
│    ├─ 后台线程：Flask（选空闲端口，127.0.0.1）   │
│    │    ├─ /api/*  → 现有查询蓝图               │
│    │    └─ /*      → 托管 app/dist（SPA 回退）  │
│    └─ 主线程：pywebview 原生窗口 → 加载本地服务   │
│                                               │
│  内嵌资源（PyInstaller datas）：               │
│    app/dist  ·  data/processed_data  ·  config │
└──────────────────────────────────────────────┘
```

- **同源**：前端由 Flask 一并托管，API 走相对路径 `/api`（见 `app/.env.production`），无跨域。
- **端口**：启动时向 OS 申请空闲端口，避免固定端口冲突。
- **资源定位**：统一经 `api/infrastructure/utils.py::resource_base()`：
  - 打包态读 `sys._MEIPASS`（PyInstaller 解包目录）；
  - 开发态读项目根目录。

## 2. 关键文件

| 文件 | 作用 |
|---|---|
| `desktop.py` | 桌面入口：起 Flask 线程 + pywebview 窗口；支持 `DESKTOP_SELFTEST=1` 无头自检 |
| `desktop.spec` | PyInstaller 配置：onedir 模式，打包资源、排除重库 |
| `app/.env.production` | `VITE_API_BASE_URL=/api`，构建时注入 |
| `requirements-desktop.txt` | 打包依赖（pywebview、pyinstaller） |
| `build_mac.sh` / `build_win.bat` | 一键构建脚本 |
| `api/infrastructure/utils.py::resource_base()` | 开发态/打包态统一资源根 |

## 3. 构建步骤

> **不能交叉编译**：macOS 产物需在 Mac 上构建，Windows 产物需在 Windows 上构建。

### 前置

```bash
conda activate dev
pip install -r requirements-desktop.txt
cd app && npm install && cd ..
```

Windows 端另需 **Microsoft Edge WebView2 Runtime**（Win10/11 多数已内置，pywebview 依赖它渲染）。

### macOS

```bash
./build_mac.sh
# 产物：dist/库存预测系统.app
open "dist/库存预测系统.app"
```

### Windows

```bat
build_win.bat
REM 产物：dist\库存预测系统.exe
```

两个脚本都是：`npm run build`（前端）→ 清理 `build/ dist/` → `pyinstaller desktop.spec`。

## 4. 验证

- **开发态**：`python desktop.py` 弹出原生窗口，数据正常加载。
- **打包态无头自检**（CI/本地冒烟）：
  ```bash
  DESKTOP_SELFTEST=1 "dist/库存预测系统.app/Contents/MacOS/库存预测系统"
  # 期望输出：[selftest] health=ok data_loaded=True stores=5 products=20
  ```
- **路径兼容单测**：`tests/test_resource_path.py`（冻结/开发两种情形）。

## 5. 体积与瘦身

在线服务仅读 CSV、不做训练，故 `desktop.spec` 的 `excludes` 排除了：
`sklearn / scipy / matplotlib`（离线计算用）、`pyarrow / sqlalchemy / psycopg2 / botocore / boto3 / s3fs / fsspec`（pandas 数据库/云存储后端）、`lxml / openpyxl / xlrd / bs4`（HTML/Excel 读取）、`PIL / bottle / aiohttp / cryptography` 等。

macOS 参考体积：**约 69MB**（瘦身前 264MB）。若新增在线依赖，记得同步复核 `excludes`。

## 6. 注意事项

- 新增需随包分发的资源目录时，在 `desktop.spec` 的 `datas` 中登记，并确保代码经 `resource_base()` 定位。
- 后端新增蓝图/仓储且为运行时动态导入时，补进 `desktop.spec` 的 `hiddenimports`，防止被漏收集。
- 数据更新流程不变：离线计算产出 `data/processed_data/*.csv` 后，重新构建即随包更新。
- macOS 未做代码签名/公证，首次打开需右键"打开"或在"系统设置 → 隐私与安全性"放行。
