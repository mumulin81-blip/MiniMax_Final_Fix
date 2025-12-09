import requests
import time

# ==================================================================
# 节点 1: A/B 轮替预清理 (Pre-Cleaner Rotation)
# ==================================================================
class MiniMaxPreCleaner:
    def __init__(self):
        pass

    @classmethod
    def INPUT_TYPES(s):
        return {
            "required": {
                # 必须连接 Seed 并在 ComfyUI 面板设置为 Increment (递增) 或 Randomize
                "seed": ("INT", {"default": 0, "min": 0, "max": 0xffffffffffffffff}),
                "api_key": ("STRING", {"multiline": False, "default": ""}),
                "group_id": ("STRING", {"multiline": False, "default": ""}),
            },
            "optional": {
                "trigger_start": ("*", {}), 
            }
        }

    RETURN_TYPES = ("STRING",)
    RETURN_NAMES = ("safe_voice_id",)
    FUNCTION = "execute_pre_clean"
    CATEGORY = "MiniMax/Workflow"

    # 强制节点每次都运行
    @classmethod
    def IS_CHANGED(s, seed, **kwargs):
        return seed

    def execute_pre_clean(self, seed, api_key, group_id, trigger_start=None):
        clean_key = api_key.strip()
        
        # === 核心逻辑：A/B 轮替 (带数字版) ===
        # 修复报错：ID 必须包含数字
        pool_index = seed % 2
        
        # 偶数用 01，奇数用 02
        # 生成的 ID 例如: "runner_slot_01"
        # 满足: 1.大于8位 2.字母开头 3.包含数字
        suffix = "01" if pool_index == 0 else "02"
        target_id = f"runner_slot_{suffix}"

        print(f"\n[MiniMax] 🔄 轮替模式: 种子[{seed}] -> 选中槽位 [{suffix}]")
        print(f"[MiniMax] 🧹 正在预清理: {target_id}")

        url = "https://api.minimax.io/v1/delete_voice"
        headers = {
            "Authorization": f"Bearer {clean_key}",
            "Content-Type": "application/json"
        }
        # 必须带 voice_type
        payload = {
            "voice_id": target_id,
            "voice_type": "voice_cloning"
        }

        # 预清理：不管存不存在，先删了再说
        try:
            requests.post(url, headers=headers, json=payload, timeout=5)
            # 稍微停顿
            time.sleep(0.5)
            print(f"[MiniMax] ✅ 场地清理完毕 ({target_id})。")
        except Exception as e:
            print(f"[MiniMax] ⚠️ 预清理网络警告: {e}")

        # 把合规的 ID 传给 Clone 节点
        return (target_id,)

# ==================================================================
# 节点 2: 后清理 (Post-Cleaner) - 保持不变
# ==================================================================
class MiniMaxPostCleaner:
    def __init__(self):
        pass
    
    @classmethod
    def INPUT_TYPES(s):
        return {
            "required": {
                "api_key": ("STRING", {"multiline": False, "default": ""}),
                "group_id": ("STRING", {"multiline": False, "default": ""}),
                "voice_id": ("STRING", {"forceInput": True}),
                "tts_output_path": ("STRING", {"forceInput": True}),
            }
        }

    RETURN_TYPES = ("STRING",)
    RETURN_NAMES = ("audio_path",)
    FUNCTION = "execute_post_clean"
    CATEGORY = "MiniMax/Workflow"
    OUTPUT_NODE = True

    def execute_post_clean(self, api_key, group_id, voice_id, tts_output_path):
        clean_key = api_key.strip()
        target_id = voice_id.strip()
        
        print(f"\n[MiniMax] 🗑️ 任务完成，执行【后清理】: {target_id}")
        
        url = "https://api.minimax.io/v1/delete_voice"
        headers = {
            "Authorization": f"Bearer {clean_key}",
            "Content-Type": "application/json"
        }
        payload = {"voice_id": target_id, "voice_type": "voice_cloning"}
        
        try:
            requests.post(url, headers=headers, json=payload, timeout=5)
            print(f"[MiniMax] ✅ 槽位已释放。")
        except:
            pass
            
        return (tts_output_path,)

NODE_CLASS_MAPPINGS = {
    "MiniMaxPreCleaner": MiniMaxPreCleaner,
    "MiniMaxPostCleaner": MiniMaxPostCleaner
}
NODE_DISPLAY_NAME_MAPPINGS = {
    "MiniMaxPreCleaner": "MiniMax 1. Pre-Cleaner (A/B)",
    "MiniMaxPostCleaner": "MiniMax 2. Post-Cleaner (End)"
}

__all__ = ['NODE_CLASS_MAPPINGS', 'NODE_DISPLAY_NAME_MAPPINGS']