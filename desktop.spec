# -*- mode: python ; coding: utf-8 -*-
"""
PyInstaller 打包配置 - desktop.spec
===================================
将后端(api) + 前端(app/dist) + 数据(data/processed_data) + 配置(config)
打包为单个桌面可执行程序。

用法：
    pyinstaller desktop.spec        # 产物在 dist/ 下

平台说明：
    - 不能交叉编译。macOS 上产出 .app / Windows 上产出 .exe，需各自本地构建。
    - excludes 掉仅离线计算才用到的重库（sklearn/scipy/matplotlib），显著减小体积。
"""

import os

# .spec 执行时工作目录即项目根目录
ROOT = os.path.abspath(os.getcwd())

datas = [
    (os.path.join(ROOT, "app", "dist"), os.path.join("app", "dist")),
    (os.path.join(ROOT, "data", "processed_data"), os.path.join("data", "processed_data")),
    (os.path.join(ROOT, "config"), "config"),
]

# 后端使用绝对导入（infrastructure/schemas/queries），需把 api/ 加入分析搜索路径
pathex = [os.path.join(ROOT, "api")]

# 蓝图与仓储多为运行时按需导入，显式声明以防被漏收集
hiddenimports = [
    "queries.overview",
    "queries.ranking",
    "queries.product_detail",
    "queries.replenishment",
    "infrastructure.dim_repository",
    "infrastructure.inventory_sales_repository",
    "infrastructure.forecast_repository",
    "infrastructure.replenishment_repository",
    "infrastructure.product_summary_repository",
    "infrastructure.sales_metrics_repository",
    "infrastructure.config_repository",
]

# 在线服务不依赖以下重库，排除以缩小体积：
#   - sklearn/scipy/matplotlib：仅离线计算/绘图用
#   - pyarrow/sqlalchemy/psycopg2/botocore/boto3/s3fs：pandas 读写数据库/云存储的可选后端，本项目仅读 CSV
#   - lxml/html5lib/bs4/openpyxl/xlrd：pandas 读 HTML/Excel 的可选依赖
#   - bottle/aiohttp：pywebview 内置 HTTP 服务器可选依赖，本项目自带 Flask，不需要
excludes = [
    "sklearn",
    "scipy",
    "matplotlib",
    "IPython",
    "notebook",
    "pytest",
    "pyarrow",
    "sqlalchemy",
    "psycopg2",
    "botocore",
    "boto3",
    "s3fs",
    "fsspec",
    "lxml",
    "html5lib",
    "bs4",
    "openpyxl",
    "xlrd",
    "bottle",
    "aiohttp",
    "cryptography",
    "PIL",
]

block_cipher = None

a = Analysis(
    ["desktop.py"],
    pathex=pathex,
    binaries=[],
    datas=datas,
    hiddenimports=hiddenimports,
    hookspath=[],
    hooksconfig={},
    runtime_hooks=[],
    excludes=excludes,
    win_no_prefer_redirects=False,
    win_private_assemblies=False,
    cipher=block_cipher,
    noarchive=False,
)

pyz = PYZ(a.pure, a.zipped_data, cipher=block_cipher)

# onedir 模式：EXE 仅含引导与脚本，二进制/资源由 COLLECT 收集到同目录。
# （官方推荐；onefile + macOS .app 已被 PyInstaller 弃用。）
exe = EXE(
    pyz,
    a.scripts,
    [],
    exclude_binaries=True,
    name="库存预测系统",
    debug=False,
    bootloader_ignore_signals=False,
    strip=False,
    upx=True,
    console=False,  # 桌面应用，不弹终端窗口
    disable_windowed_traceback=False,
    argv_emulation=False,
    target_arch=None,
    codesign_identity=None,
    entitlements_file=None,
)

coll = COLLECT(
    exe,
    a.binaries,
    a.zipfiles,
    a.datas,
    strip=False,
    upx=True,
    upx_exclude=[],
    name="库存预测系统",
)

# macOS：额外产出 .app 包，便于双击与 Dock 展示
app = BUNDLE(
    coll,
    name="库存预测系统.app",
    icon=None,
    bundle_identifier="com.sephora.inventory-forecast",
)

