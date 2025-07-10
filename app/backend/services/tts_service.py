"""
TTS语音合成服务
"""

import asyncio
import os
from typing import List, Dict
from pathlib import Path
from core.config import settings

class TTSService:
    """TTS服务类"""
    
    def __init__(self):
        self.engine = settings.TTS_ENGINE
        self.voice_host = settings.TTS_VOICE_HOST
        self.voice_guest = settings.TTS_VOICE_GUEST
        
        # 确保输出目录存在
        Path(settings.PODCAST_DIR).mkdir(parents=True, exist_ok=True)
    
    async def synthesize_text(self, text: str, voice: str = None, output_file: str = None) -> str:
        """合成单段文本"""
        if not voice:
            voice = self.voice_host
        
        if not output_file:
            import time
            output_file = f"{settings.PODCAST_DIR}/tts_{int(time.time())}.wav"
        
        try:
            if self.engine == "edge":
                return await self._edge_tts_synthesize(text, voice, output_file)
            else:
                raise ValueError(f"不支持的TTS引擎: {self.engine}")
        except Exception as e:
            print(f"TTS合成失败: {e}")
            return None
    
    async def _edge_tts_synthesize(self, text: str, voice: str, output_file: str) -> str:
        """使用Edge TTS合成语音"""
        try:
            import edge_tts
            
            # 创建TTS通信对象
            communicate = edge_tts.Communicate(text, voice)
            
            # 合成并保存
            await communicate.save(output_file)
            
            return output_file
        except ImportError:
            print("❌ edge-tts 库未安装")
            return None
        except Exception as e:
            print(f"Edge TTS合成失败: {e}")
            return None
    
    async def synthesize_podcast(self, script: Dict, output_file: str = None) -> str:
        """合成完整播客"""
        if not output_file:
            import time
            output_file = f"{settings.PODCAST_DIR}/podcast_{int(time.time())}.mp3"
        
        try:
            # 创建临时音频文件列表
            temp_files = []
            
            # 处理脚本段落
            segments = script.get("segments", [])
            if not segments and "content" in script:
                # 简单文本格式，按句子分割
                segments = [{"speaker": "主持人", "content": script["content"]}]
            
            for i, segment in enumerate(segments):
                speaker = segment.get("speaker", "主持人")
                content = segment.get("content", "")
                
                if not content.strip():
                    continue
                
                # 选择声音
                voice = self.voice_host if "主持人" in speaker else self.voice_guest
                
                # 生成临时文件
                temp_file = f"{settings.PODCAST_DIR}/temp_segment_{i}.wav"
                result_file = await self.synthesize_text(content, voice, temp_file)
                
                if result_file:
                    temp_files.append(result_file)
            
            if not temp_files:
                print("❌ 没有成功合成的音频段")
                return None
            
            # 合并音频文件
            merged_file = await self._merge_audio_files(temp_files, output_file)
            
            # 清理临时文件
            for temp_file in temp_files:
                try:
                    os.remove(temp_file)
                except:
                    pass
            
            return merged_file
            
        except Exception as e:
            print(f"播客合成失败: {e}")
            return None
    
    async def _merge_audio_files(self, audio_files: List[str], output_file: str) -> str:
        """合并多个音频文件"""
        try:
            from pydub import AudioSegment
            
            # 加载第一个文件
            merged = AudioSegment.from_wav(audio_files[0])
            
            # 逐个合并其他文件，中间添加短暂停顿
            silence = AudioSegment.silent(duration=500)  # 0.5秒停顿
            
            for audio_file in audio_files[1:]:
                audio = AudioSegment.from_wav(audio_file)
                merged = merged + silence + audio
            
            # 导出为MP3
            merged.export(output_file, format="mp3", bitrate="128k")
            
            return output_file
            
        except ImportError:
            print("❌ pydub 库未安装")
            # 简单复制第一个文件作为回退
            import shutil
            shutil.copy(audio_files[0], output_file)
            return output_file
        except Exception as e:
            print(f"音频合并失败: {e}")
            return None

# 全局TTS服务实例
tts_service = TTSService()

async def generate_podcast_audio(script: Dict, title: str = "podcast") -> str:
    """生成播客音频文件"""
    import time
    filename = f"podcast_{title}_{int(time.time())}.mp3"
    output_path = f"{settings.PODCAST_DIR}/{filename}"
    
    result = await tts_service.synthesize_podcast(script, output_path)
    return result 