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

    def _delete_voice(self, api_key: str, voice_id: str, retry: int = 1):
        """调用删除接口，带简单重试与状态校验。"""
        clean_key = api_key.strip()
        if not clean_key:
            raise ValueError("[MiniMax] api_key 不能为空")

        url = "https://api.minimax.io/v1/delete_voice"
        headers = {
            "Authorization": f"Bearer {clean_key}",
            "Content-Type": "application/json"
        }
        payload = {"voice_id": voice_id, "voice_type": "voice_cloning"}

        last_err = None
        for attempt in range(retry + 1):
            try:
                resp = requests.post(url, headers=headers, json=payload, timeout=(3, 5))
                if resp.status_code < 400:
                    # 204/200/404 都视为已清理完成
                    return True
                # 记录错误文本方便排查
                last_err = f"status={resp.status_code}, body={resp.text}"
            except Exception as e:
                last_err = str(e)

            if attempt < retry:
                time.sleep(0.3 * (attempt + 1))

        print(f"[MiniMax] ⚠️ 清理失败: voice_id={voice_id}, err={last_err}")
        return False

    def execute_pre_clean(self, seed, api_key, group_id, trigger_start=None):
        # === 核心逻辑：A/B 轮替 (带数字版) ===
        pool_index = seed % 2

        suffix = "01" if pool_index == 0 else "02"
        target_id = f"runner_slot_{suffix}"

        print(f"\n[MiniMax] 🔄 轮替模式: 种子[{seed}] -> 选中槽位 [{suffix}]")
        print(f"[MiniMax] 🧹 正在预清理: {target_id}")

        # 预清理：不管存不存在，先删了再说
        success = self._delete_voice(api_key, target_id, retry=1)
        if success:
            print(f"[MiniMax] ✅ 场地清理完毕 ({target_id})。")
        else:
            print(f"[MiniMax] ⚠️ 场地清理未确认 ({target_id})，后续可能冲突。")

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
        target_id = voice_id.strip()
        
        print(f"\n[MiniMax] 🗑️ 任务完成，执行【后清理】: {target_id}")

        success = MiniMaxPreCleaner()._delete_voice(api_key, target_id, retry=1)
        if success:
            print(f"[MiniMax] ✅ 槽位已释放。")
        else:
            print(f"[MiniMax] ⚠️ 槽位释放失败: {target_id}，请手动检查。")
            
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