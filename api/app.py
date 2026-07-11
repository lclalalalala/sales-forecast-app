"""
零售门店库存与需求预测系统 - Flask REST API
==========================================
提供门店、商品、销售趋势、补货建议等数据接口。
"""

import os
import sys
from datetime import datetime, timedelta
from flask import Flask, jsonify, request
from flask_cors import CORS

# 将项目根目录加入路径
project_root = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, project_root)

from services.data_service import DataService
from services.forecast_service import ForecastService

# ─── Flask 应用初始化 ──────────────────────────────────────────
app = Flask(__name__)
CORS(app, resources={r"/api/*": {"origins": "*"}})

# ─── 服务实例 (单例模式) ───────────────────────────────────────
# 数据集路径
data_path = os.path.join(os.path.dirname(project_root), "data", "sales_data.csv")
data_service = DataService(data_path)
forecast_service = ForecastService()


# ═══════════════════════════════════════════════════════════════
# 辅助函数
# ═══════════════════════════════════════════════════════════════
def format_response(data, success=True, message=""):
    """统一响应格式"""
    return jsonify({
        "success": success,
        "data": data,
        "message": message,
        "timestamp": datetime.now().isoformat()
    })


def handle_error(error_msg, status_code=500):
    """统一错误处理"""
    return format_response(None, success=False, message=str(error_msg)), status_code


# ═══════════════════════════════════════════════════════════════
# API 路由
# ═══════════════════════════════════════════════════════════════

@app.route("/api/health", methods=["GET"])
def health_check():
    """健康检查接口"""
    return format_response({
        "status": "ok",
        "data_loaded": data_service.is_loaded(),
        "stores_count": len(data_service.get_stores()),
        "products_count": len(data_service.get_products())
    })


# ─── 门店相关接口 ──────────────────────────────────────────────

@app.route("/api/stores", methods=["GET"])
def get_stores():
    """获取所有门店列表"""
    try:
        stores = data_service.get_stores()
        return format_response([{
            "id": s["id"],
            "name": f"门店 {s['id']}",
            "region": s["region"]
        } for s in stores])
    except Exception as e:
        return handle_error(e)


# ─── 商品相关接口 ──────────────────────────────────────────────

@app.route("/api/categories", methods=["GET"])
def get_categories():
    """获取所有商品类别列表"""
    try:
        categories = data_service.get_categories()
        return format_response(categories)
    except Exception as e:
        return handle_error(e)


@app.route("/api/products", methods=["GET"])
def get_products():
    """获取商品列表，可按门店和类别筛选"""
    try:
        store_id = request.args.get("store_id")
        category = request.args.get("category")
        products = data_service.get_products(store_id, category=category)
        return format_response([{
            "id": p["id"],
            "name": p["id"],
            "category": p["category"]
        } for p in products])
    except Exception as e:
        return handle_error(e)


# ─── 销售趋势接口 ──────────────────────────────────────────────

@app.route("/api/sales/trend", methods=["GET"])
def get_sales_trend():
    """获取门店销售趋势（过去N天），支持类别筛选"""
    try:
        store_id = request.args.get("store_id", "S001")
        days = int(request.args.get("days", 90))
        category = request.args.get("category")

        trend_data = data_service.get_sales_trend(store_id, days, category=category)

        # 计算汇总指标
        total_units = sum(d["units_sold"] for d in trend_data)
        avg_daily = total_units / len(trend_data) if trend_data else 0

        # 计算增长率 (前半月 vs 后半月)
        mid = len(trend_data) // 2
        if mid > 0:
            first_half = sum(d["units_sold"] for d in trend_data[:mid]) / mid
            second_half = sum(d["units_sold"] for d in trend_data[mid:]) / (len(trend_data) - mid)
            growth_rate = round((second_half - first_half) / first_half, 4) if first_half > 0 else 0
        else:
            growth_rate = 0

        return format_response({
            "daily_sales": trend_data,
            "summary": {
                "total_units_sold": total_units,
                "avg_daily_sales": round(avg_daily, 1),
                "growth_rate": growth_rate,
                "data_points": len(trend_data)
            }
        })
    except Exception as e:
        return handle_error(e)


# ─── 商品排名接口 ──────────────────────────────────────────────

@app.route("/api/sales/ranking", methods=["GET"])
def get_sales_ranking():
    """获取商品销量排名 (Top 5 + Bottom 5)，支持类别和库存状态筛选"""
    try:
        store_id = request.args.get("store_id", "S001")
        days = int(request.args.get("days", 90))
        category = request.args.get("category")
        inventory_status = request.args.get("inventory_status")

        ranking = data_service.get_product_ranking(
            store_id, days, category=category, inventory_status=inventory_status
        )

        return format_response({
            "top_5": [{
                "rank": i + 1,
                "product_id": r["product_id"],
                "category": r["category"],
                "total_sold": r["total_sold"],
                "avg_daily": r["avg_daily"],
                "inventory": r.get("inventory"),
                "inventory_status": r.get("inventory_status")
            } for i, r in enumerate(ranking["top_5"])],
            "bottom_5": [{
                "rank": i + 1,
                "product_id": r["product_id"],
                "category": r["category"],
                "total_sold": r["total_sold"],
                "avg_daily": r["avg_daily"],
                "inventory": r.get("inventory"),
                "inventory_status": r.get("inventory_status")
            } for i, r in enumerate(ranking["bottom_5"])]
        })
    except Exception as e:
        return handle_error(e)


# ─── 补货建议接口 ──────────────────────────────────────────────

@app.route("/api/replenishment", methods=["GET"])
def get_replenishment_suggestions():
    """获取 Top 5 畅销品的补货建议"""
    try:
        store_id = request.args.get("store_id", "S001")
        safety_factor = float(request.args.get("safety_factor", 1.2))

        # 获取该门店数据
        store_data = data_service.get_store_data(store_id)

        # 获取 Top 5 畅销品
        ranking = data_service.get_product_ranking(store_id, days=90)
        top_5_products = ranking["top_5"]

        suggestions = []
        for product in top_5_products:
            pid = product["product_id"]

            # 获取该商品的历史数据
            product_data = data_service.get_product_history(store_id, pid, days=90)

            # 预测未来7天需求
            predictions = forecast_service.predict_next_7_days(product_data)
            total_predicted = round(sum(predictions), 1)

            # 获取当前库存
            current_inventory = data_service.get_current_inventory(store_id, pid)

            # 计算建议补货量
            suggested_qty = max(0, round(total_predicted * safety_factor - current_inventory, 1))

            suggestions.append({
                "product_id": pid,
                "category": product["category"],
                "current_inventory": current_inventory,
                "predicted_demand_7d": predictions,
                "total_predicted_demand": total_predicted,
                "suggested_replenishment": suggested_qty,
                "confidence": "high" if len(product_data) >= 60 else "medium"
            })

        return format_response({
            "store_id": store_id,
            "forecast_date": (datetime.now() + timedelta(days=1)).strftime("%Y-%m-%d"),
            "safety_factor": safety_factor,
            "top_5_products": suggestions
        })
    except Exception as e:
        return handle_error(e)


# ─── 商品详情接口 ──────────────────────────────────────────────

@app.route("/api/products/detail", methods=["GET"])
def get_product_detail():
    """获取商品详细信息（历史销售 + 预测 + 补货建议）"""
    try:
        store_id = request.args.get("store_id", "S001")
        product_id = request.args.get("product_id", "P0001")
        days = int(request.args.get("days", 90))
        safety_factor = float(request.args.get("safety_factor", 1.2))

        # 获取商品历史数据
        history = data_service.get_product_history(store_id, product_id, days)

        # 获取商品基本信息
        product_info = data_service.get_product_info(store_id, product_id)

        # 预测未来7天
        predictions = forecast_service.predict_next_7_days(history)
        total_predicted = round(sum(predictions), 1)

        # 当前库存
        current_inventory = data_service.get_current_inventory(store_id, product_id)

        # 补货建议
        suggested_qty = max(0, round(total_predicted * safety_factor - current_inventory, 1))

        return format_response({
            "product_id": product_id,
            "category": product_info["category"],
            "price": product_info["price"],
            "current_inventory": current_inventory,
            "historical_sales": [{
                "date": h["date"],
                "units_sold": h["units_sold"],
                "demand": h["demand"],
                "inventory": h["inventory"]
            } for h in history],
            "forecast": {
                "next_7_days": predictions,
                "total_predicted": total_predicted,
                "suggested_replenishment": suggested_qty,
                "safety_factor": safety_factor
            }
        })
    except Exception as e:
        return handle_error(e)


# ─── KPI 汇总接口 ──────────────────────────────────────────────

@app.route("/api/dashboard/kpi", methods=["GET"])
def get_dashboard_kpi():
    """获取数据概览页 KPI 数据"""
    try:
        store_id = request.args.get("store_id", "S001")
        days = int(request.args.get("days", 90))

        # 销售趋势
        trend = data_service.get_sales_trend(store_id, days)
        total_units = sum(d["units_sold"] for d in trend)
        avg_daily = total_units / len(trend) if trend else 0

        # 获取商品数
        products = data_service.get_products(store_id)

        # 获取总需求量
        total_demand = sum(d["demand"] for d in trend)

        # 计算库存周转率 (总销量 / 平均库存)
        avg_inventory = data_service.get_avg_inventory(store_id, days)
        turnover = total_units / avg_inventory if avg_inventory > 0 else 0

        return format_response({
            "store_id": store_id,
            "period_days": days,
            "total_sales": total_units,
            "total_demand": total_demand,
            "avg_daily_sales": round(avg_daily, 1),
            "active_products": len(products),
            "avg_inventory": round(avg_inventory, 1),
            "inventory_turnover": round(turnover, 2)
        })
    except Exception as e:
        return handle_error(e)


# ═══════════════════════════════════════════════════════════════
# 启动入口
# ═══════════════════════════════════════════════════════════════

if __name__ == "__main__":
    print("=" * 60)
    print("零售门店库存与需求预测系统 API 服务")
    print("=" * 60)
    print(f"数据集路径: {data_path}")
    print(f"数据加载状态: {'成功' if data_service.is_loaded() else '失败'}")
    print(f"门店数量: {len(data_service.get_stores())}")
    print(f"商品数量: {len(data_service.get_products())}")
    print("-" * 60)
    print("API 端点:")
    print("  GET /api/health              - 健康检查")
    print("  GET /api/stores              - 门店列表")
    print("  GET /api/products            - 商品列表")
    print("  GET /api/sales/trend         - 销售趋势")
    print("  GET /api/sales/ranking       - 商品排名")
    print("  GET /api/replenishment       - 补货建议")
    print("  GET /api/products/detail     - 商品详情")
    print("  GET /api/dashboard/kpi       - KPI汇总")
    print("=" * 60)
    app.run(host="0.0.0.0", port=8999, debug=True)
