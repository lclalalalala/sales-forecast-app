"""
响应组装 - Responses
===================
统一构造 `{context, data}` 响应与 `{error}` 错误响应。
"""

from typing import Any, Dict

from flask import jsonify, Response


def build_response(context: Dict[str, Any], data: Any) -> Response:
    """构造成功响应。"""
    return jsonify({
        "context": context,
        "data": data,
    })


def build_error(code: str, message: str, status_code: int = 400) -> tuple[Response, int]:
    """构造错误响应。"""
    return jsonify({
        "error": {
            "code": code,
            "message": message,
        }
    }), status_code


def build_internal_error(message: str) -> tuple[Response, int]:
    """构造 500 错误响应。"""
    return build_error("INTERNAL_ERROR", message, 500)
