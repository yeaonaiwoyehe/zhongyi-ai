from flask import Flask, request, jsonify
from flask_cors import CORS
import os
import json
import uuid

from feature_extractor import extract_feature
from search import search

# 👉 如果你有AI接口，就用这个（没有也能跑）
USE_AI = False

if USE_AI:
    from ai_fallback import call_ai_api

app = Flask(__name__)
CORS(app)

UPLOAD_FOLDER = "temp"
os.makedirs(UPLOAD_FOLDER, exist_ok=True)

THRESHOLD = 0.6  # ⭐ 可以调（0.6~0.75）

# 加载知识库
with open("knowledge.json", "r", encoding="utf-8") as f:
    knowledge = json.load(f)


@app.route('/')
def home():
    return "🚀 后端运行中（升级版）"


@app.route('/upload', methods=['POST'])
def upload():
    if 'image' not in request.files:
        return jsonify({"success": False, "message": "未上传图片"})

    file = request.files['image']

    # 保存图片
    filename = str(uuid.uuid4()) + ".jpg"
    filepath = os.path.join(UPLOAD_FOLDER, filename)
    file.save(filepath)

    try:
        # 🧠 提取特征
        feat = extract_feature(filepath)

        # 🔍 检索
        result = search(feat)

        similarity = result["similarity"]
        img_id = result["image"]

        # ===============================
        # 🔥 核心升级：双引擎判断
        # ===============================
        if similarity >= THRESHOLD:
            # ✅ 命中数据库
            info = knowledge.get(img_id, {})

            response = {
                "success": True,
                "message": "识别成功（数据库匹配）",
                "source": "database",
                "top1": {
                    "image_id": img_id,
                    "similarity": similarity,
                    **info
                }
            }

        else:
            # 🤖 AI兜底
            if USE_AI:
                ai_result = call_ai_api(filepath)
            else:
                # 👉 没有API时用这个（推荐你现在用）
                ai_result = {
                    "name": "未知中医器具",
                    "dynasty": "待考证",
                    "usage": "该器具可能用于中药加工、捣碎或储存",
                    "story": "系统未匹配到相关文物，以下内容为AI生成，仅供参考"
                }

            response = {
                "success": True,
                "message": "未匹配到数据库，使用AI生成",
                "source": "ai",
                "similarity": similarity,
                **ai_result
            }

        # 返回中文正常显示
        return app.response_class(
            response=json.dumps(response, ensure_ascii=False),
            mimetype='application/json'
        )

    except Exception as e:
        return jsonify({
            "success": False,
            "message": str(e)
        })


if __name__ == '__main__':
    app.run(debug=True)