"""
零售门店库存与需求预测系统 - Flask REST API
==========================================
新版入口：注册基于离线预计算架构的查询蓝图，统一 `{context, data}` 响应结构。

路由清单（详见 project_docs/07-API.md）：
  GET /api/health                 - 健康检查
  GET /api/stores                 - 门店列表
  GET /api/categories             - 商品类别列表
  GET /api/products               - 商品列表            (queries/product_detail.py)
  GET /api/products/<product_id>  - 商品详情            (queries/product_detail.py)
  GET /api/overview               - 数据概览            (queries/overview.py)
  GET /api/rankings               - 商品排名            (queries/ranking.py)
  GET /api/replenishment          - 补货建议            (queries/replenishment.py)
"""

import os
import sys

from flask import Flask, request
from flask_cors import CORS

# 将 api/ 目录加入路径，使蓝图的绝对导入（infrastructure/schemas/queries）可解析
project_root = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, project_root)

from infrastructure.dim_repository import dim_repository
from infrastructure.inventory_sales_repository import inventory_sales_repository
from infrastructure.utils import resource_base
from schemas import responses
from queries.overview import overview_bp
from queries.ranking import ranking_bp
from queries.product_detail import product_bp
from queries.replenishment import replenishment_bp


# ─── Flask 应用初始化 ──────────────────────────────────────────
# static_folder 指向前端构建产物 app/dist（打包态由 resource_base 定位到解包目录）。
# static_url_path="" 使 /assets/*.js、/*.css 等静态资源直接从根路径提供。
_DIST_DIR = os.path.join(resource_base(), "app", "dist")
app = Flask(__name__, static_folder=_DIST_DIR, static_url_path="")
# 桌面打包为同源访问，CORS 仅对开发态（前端 3000、后端独立端口）有意义，保留无副作用。
CORS(app, resources={r"/api/*": {"origins": "*"}})

# ─── 注册查询蓝图 ──────────────────────────────────────────────
app.register_blueprint(overview_bp)
app.register_blueprint(ranking_bp)
app.register_blueprint(product_bp)
app.register_blueprint(replenishment_bp)


# ─── 前端托管（SPA）───────────────────────────────────────────

@app.route("/")
def _spa_index():
    """根路径返回前端入口页。"""
    return app.send_static_file("index.html")


@app.errorhandler(404)
def _spa_fallback(err):
    """未命中的路径：
    - /api/* 未匹配 → 返回结构化 404 错误。
    - 其余（前端路由，如 /products/xxx）→ 回退到 index.html，交由 React Router 处理。
    """
    if request.path.startswith("/api/"):
        return responses.build_error("NOT_FOUND", "接口不存在", 404)
    index_path = os.path.join(_DIST_DIR, "index.html")
    if os.path.isfile(index_path):
        return app.send_static_file("index.html")
    return err


# ─── 元数据接口（蓝图未覆盖，context=null）────────────────────

@app.route("/api/health", methods=["GET"])
def health_check():
    """健康检查：返回预计算数据加载状态与维表统计。"""
    try:
        counts = dim_repository.counts()
        data_loaded = dim_repository.is_loaded() and inventory_sales_repository.is_loaded()
        return responses.build_response(None, {
            "status": "ok" if data_loaded else "degraded",
            "data_loaded": data_loaded,
            "stores_count": counts["stores"],
            "products_count": counts["products"],
            "categories_count": counts["categories"],
        })
    except Exception as e:
        return responses.build_internal_error(str(e))


@app.route("/api/stores", methods=["GET"])
def get_stores():
    """门店列表，用于前端门店筛选下拉框。"""
    try:
        stores = dim_repository.get_stores()
        return responses.build_response(None, [
            {"id": s["id"], "name": s["name"], "region": s["region"]}
            for s in stores
        ])
    except Exception as e:
        return responses.build_internal_error(str(e))


@app.route("/api/categories", methods=["GET"])
def get_categories():
    """商品类别列表，用于前端类别筛选。"""
    try:
        return responses.build_response(None, dim_repository.get_categories())
    except Exception as e:
        return responses.build_internal_error(str(e))


# ─── 启动入口 ──────────────────────────────────────────────────

if __name__ == "__main__":
    counts = dim_repository.counts()
    data_loaded = dim_repository.is_loaded() and inventory_sales_repository.is_loaded()
    print("=" * 60)
    print("零售门店库存与需求预测系统 API 服务（离线预计算架构）")
    print("=" * 60)
    print(f"预计算数据加载状态: {'成功' if data_loaded else '失败'}")
    print(f"门店数量: {counts['stores']}")
    print(f"商品数量: {counts['products']}")
    print(f"类别数量: {counts['categories']}")
    print("-" * 60)
    print("API 端点:")
    print("  GET /api/health                 - 健康检查")
    print("  GET /api/stores                 - 门店列表")
    print("  GET /api/categories             - 商品类别列表")
    print("  GET /api/products               - 商品列表")
    print("  GET /api/products/<product_id>  - 商品详情")
    print("  GET /api/overview               - 数据概览")
    print("  GET /api/rankings               - 商品排名")
    print("  GET /api/replenishment          - 补货建议")
    print("=" * 60)
    app.run(host="0.0.0.0", port=8999, debug=True)
