# translator.py
from sentence_transformers import SentenceTransformer, util
import torch
import os

class ToolTranslator:
    def __init__(self, available_tools):
        """
        available_tools: 传入你的 TOOLS.keys()，例如 ['sphere', 'cylinder', 'translate', 'common', 'cut', 'fuse']
        """
        # 加载轻量级模型 (all-MiniLM-L6-v2)
        # 第一次运行会下载，约 80MB。它是目前性价比最高的语义匹配模型。
        print("🚀 正在加载语义向量模型...")
        self.model = SentenceTransformer('all-MiniLM-L6-v2')
        
        self.standard_tools = list(available_tools)
        
        # 预先计算标准工具的向量 (Embeddings)，存入内存以备比对
        self.tool_embeddings = self.model.encode(self.standard_tools, convert_to_tensor=True)
        print(f"✅ 语义翻译官已就绪。已注册工具: {self.standard_tools}")

    def translate(self, ai_tool_name, threshold=0.5):
        """
        将 AI 可能乱起的工具名翻译成标准工具名
        ai_tool_name: AI 输出的 raw tool name
        threshold: 相似度阈值。如果相似度低于这个值，说明匹配失败。
        """

        if not ai_tool_name:
            return None
            
        raw_name = ai_tool_name.lower().strip()

        if "vis" in raw_name: return "visibility" # 强制保护关键词

        # 1. 精确匹配优先（性能最高）
        if raw_name in self.standard_tools:
            return raw_name
            
        # 2. 特殊情况处理 (Boolean 逻辑映射)
        # 因为 AI 有时会把操作放在 args 里，这里做一个简单的预处理
        if "intersect" in raw_name: return "common"
        if "minus" in raw_name or "subtract" in raw_name: return "cut"
        if "union" in raw_name or "combine" in raw_name: return "fuse"
        if "move" in raw_name: return "translate"

        # 3. 语义向量匹配 (Embedding)
        query_embedding = self.model.encode(raw_name, convert_to_tensor=True)
        
        # 计算余弦相似度
        cos_scores = util.cos_sim(query_embedding, self.tool_embeddings)[0]
        
        # 找到得分最高的工具
        best_idx = torch.argmax(cos_scores).item()
        best_score = cos_scores[best_idx].item()

        print(f"🔍 语义比对: AI输入='{raw_name}', 匹配到='{self.standard_tools[best_idx]}', 相似度={best_score:.2f}")

        # 如果相似度达标，则返回标准名
        if best_score >= threshold:
            return self.standard_tools[best_idx]
        
        return raw_name  # 匹配度太低则原样返回，由后续逻辑报错