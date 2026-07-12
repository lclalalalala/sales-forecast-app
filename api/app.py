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

from flask import Flask
from flask_cors import CORS

# 将 api/ 目录加入路径，使蓝图的绝对导入（infrastructure/schemas/queries）可解析
project_root = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, project_root)

from infrastructure.csv_repository import csv_repository
from schemas import responses
from queries.overview import overview_bp
from queries.ranking import ranking_bp
from queries.product_detail import product_bp
from queries.replenishment import replenishment_bp


# ─── Flask 应用初始化 ──────────────────────────────────────────
app = Flask(__name__)
CORS(app, resources={r"/api/*": {"origins": "*"}})

# ─── 注册查询蓝图 ──────────────────────────────────────────────
app.register_blueprint(overview_bp)
app.register_blueprint(ranking_bp)
app.register_blueprint(product_bp)
app.register_blueprint(replenishment_bp)


# ─── 元数据接口（蓝图未覆盖，context=null）────────────────────

@app.route("/api/health", methods=["GET"])
def health_check():
    """健康检查：返回数据加载状态与数据集统计。"""
    try:
        summary = csv_repository.get_summary()
        return responses.build_response(None, {
            "status": "ok",
            "data_loaded": csv_repository.is_loaded(),
            "stores_count": summary.get("stores", 0),
            "products_count": summary.get("products", 0),
            "categories_count": summary.get("categories", 0),
        })
    except Exception as e:
        return responses.build_internal_error(str(e))


@app.route("/api/stores", methods=["GET"])
def get_stores():
    """门店列表，用于前端门店筛选下拉框。"""
    try:
        stores = csv_repository.get_stores()
        return responses.build_response(None, [
            {"id": s["id"], "name": f"门店 {s['id']}", "region": s["region"]}
            for s in stores
        ])
    except Exception as e:
        return responses.build_internal_error(str(e))


@app.route("/api/categories", methods=["GET"])
def get_categories():
    """商品类别列表，用于前端类别筛选。"""
    try:
        return responses.build_response(None, csv_repository.get_categories())
    except Exception as e:
        return responses.build_internal_error(str(e))


# ─── 启动入口 ──────────────────────────────────────────────────

if __name__ == "__main__":
    summary = csv_repository.get_summary()
    print("=" * 60)
    print("零售门店库存与需求预测系统 API 服务（离线预计算架构）")
    print("=" * 60)
    print(f"数据加载状态: {'成功' if csv_repository.is_loaded() else '失败'}")
    print(f"门店数量: {summary.get('stores', 0)}")
    print(f"商品数量: {summary.get('products', 0)}")
    print(f"类别数量: {summary.get('categories', 0)}")
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
