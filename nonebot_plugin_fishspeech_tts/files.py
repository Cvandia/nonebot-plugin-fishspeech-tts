import re
from pathlib import Path

from nonebot.log import logger

from .exception import FileHandleException
from .request_params import ServeReferenceAudio

# 音频文件后缀
AUDIO_FILE_SUFFIX = [
    ".mp3",
    ".wav",
    ".flac",
    ".ogg",
    ".m4a",
    ".wma",
    ".aac",
    ".aiff",
    ".aif",
    ".aifc",
]


def extract_text_by_filename(file_name: str) -> str:
    """
    从文件名中提取文本标签

    Args:
        file_name: 文件名
    Returns:
        ref_text: 提取的文本标签

    exception:
        FileHandleException: 未能从文件名中提取文本标签
    """

    ref_text = re.sub(r"\[.*\]", "", file_name)
    ref_text = Path(ref_text).stem
    if not ref_text:
        raise FileHandleException(f"未能从文件名{file_name}中提取文本标签")
    return ref_text


def get_speaker_audio_path(path_audio: Path, speaker_name: str) -> list[Path]:
    """
    获取指定说话人的音频文件路径

    Args:
        speaker_name: 说话人姓名
        path_audio: 音频文件路径
    Returns:
        speaker_audio_path: 说话人音频文件路径列表

    exception:
        FileHandleException: 未找到说话人音频文件
    """

    try:
        speaker_audio_path = [
            audio
            for audio in path_audio.iterdir()
            if audio.is_file()
            and speaker_name in audio.name
            and audio.suffix.lower() in AUDIO_FILE_SUFFIX
        ]
    except OSError as exc:
        raise FileHandleException("参考音频目录不存在或无法读取") from exc
    logger.debug(f"获取到角色的语音路劲: {speaker_audio_path}")
    if not speaker_audio_path:
        raise FileHandleException(f"未找到角色:{speaker_name}的音频文件")
    return speaker_audio_path


def get_path_speaker_list(path_audio: Path) -> list[str]:
    """
    获取说话人列表

    Returns:
        list[str]: 说话人列表

    exception:
        FileHandleException: 未找到说话人
    """
    speaker_list = []
    try:
        for audio in path_audio.iterdir():
            if audio.is_file() and audio.suffix.lower() in AUDIO_FILE_SUFFIX:
                speaker_name = re.search(r"\[(.*)\]", audio.stem)
                if speaker_name:
                    speaker_list.append(speaker_name.group(1))
    except OSError as exc:
        raise FileHandleException("参考音频目录不存在或无法读取") from exc
    # 去重
    speaker_list = list(set(speaker_list))
    if not speaker_list:
        raise FileHandleException("未找到说话人音频文件")
    return speaker_list


def load_references(path_audio: Path, speaker_name: str) -> list[ServeReferenceAudio]:
    try:
        return [
            ServeReferenceAudio(
                audio=audio.read_bytes(), text=extract_text_by_filename(audio.name)
            )
            for audio in get_speaker_audio_path(path_audio, speaker_name)
        ]
    except OSError as exc:
        raise FileHandleException("参考音频文件无法读取") from exc
