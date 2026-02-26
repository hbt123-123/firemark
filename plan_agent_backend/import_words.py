#!/usr/bin/env python3
"""
单词数据导入脚本

用法:
    python import_words.py <json_file> [--tag TAG] [--difficulty DIFFICULTY]

参数:
    json_file: JSON文件路径 (必需)
    --tag: 可选标签过滤，如 "四级"、"六级"、"IELTS"、"托福"、"考研"
    --difficulty: 难度等级 (1=CET4, 2=CET6, 3=托福, 4=IELTS, 5=考研)

示例:
    python import_words.py word_format/CET4-顺序.json --tag 四级 --difficulty 1
    python import_words.py word_format/IELTS-顺序.json --tag IELTS --difficulty 4
    python import_words.py word_format/CET4-顺序.json  # 无标签过滤
"""

import argparse
import json
import os
import sys
from pathlib import Path

from dotenv import load_dotenv
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

# 加载环境变量
load_dotenv()

# 添加项目路径
sys.path.insert(0, str(Path(__file__).parent))

from app.models import WordBank


# 添加项目路径
sys.path.insert(0, str(Path(__file__).parent))

from app.models import WordBank



def parse_json_file(file_path: str) -> list[dict]:
    """解析JSON文件并返回单词列表"""
    with open(file_path, "r", encoding="utf-8") as f:
        data = json.load(f)
    return data


def normalize_part_of_speech(pos: str) -> str | None:
    """标准化词性格式"""
    if not pos:
        return None
    # 移除末尾的点号，如 "n." -> "n", "v." -> "v"
    return pos.rstrip(".")


def generate_audio_urls(word: str) -> tuple[str, str]:
    """生成占位音频URL"""
    # 格式: /audio/word_en.mp3, /audio/word_zh.mp3
    audio_en = f"/audio/{word.lower()}_en.mp3"
    audio_zh = f"/audio/{word.lower()}_zh.mp3"
    return audio_en, audio_zh


def transform_word_data(
    word_item: dict,
    tag: str | None = None,
    difficulty: int = 1,
) -> dict | None:
    """
    转换单个单词数据为数据库格式

    处理IELTS和其他格式的差异:
    - IELTS有pronunciation字段，其他没有
    - translations数组需要合并为单一translation + part_of_speech
    """
    word = word_item.get("word", "").strip()
    if not word:
        return None

    # 获取翻译和词性
    translations = word_item.get("translations", [])
    if translations and len(translations) > 0:
        # 取第一个翻译作为主翻译
        first_trans = translations[0]
        translation = first_trans.get("translation", "")
        part_of_speech = normalize_part_of_speech(first_trans.get("type"))
    else:
        translation = ""
        part_of_speech = None

    # IELTS格式有pronunciation字段，其他格式没有
    pronunciation = word_item.get("pronunciation")

    # 生成音频URL
    audio_en, audio_zh = generate_audio_urls(word)

    # 构建tags
    tags = []
    if tag:
        tags.append(tag)

    # 例句可以从translations中提取（如果有多个翻译，可以把其他翻译作为例句）
    examples = None
    if len(translations) > 1:
        examples = [
            {"translation": t.get("translation", ""), "type": t.get("type", "")}
            for t in translations[1:]
        ]

    return {
        "word": word,
        "pronunciation": pronunciation,
        "translation": translation,
        "part_of_speech": part_of_speech,
        "examples": examples,
        "audio_url_en": audio_en,
        "audio_url_zh": audio_zh,
        "difficulty": difficulty,
        "tags": tags if tags else None,
    }


def import_words(
    session,
    words_data: list[dict],
    tag: str | None = None,
    difficulty: int = 1,
) -> tuple[int, int]:
    """
    导入单词数据

    返回: (成功数量, 跳过数量)
    """
    success_count = 0
    skip_count = 0

    for word_item in words_data:
        try:
            word_data = transform_word_data(word_item, tag, difficulty)
            if not word_data:
                skip_count += 1
                continue

            # 检查单词是否已存在
            existing = (
                session.query(WordBank)
                .filter(WordBank.word == word_data["word"])
                .first()
            )

            if existing:
                # 可选：更新已存在的单词
                # for key, value in word_data.items():
                #     setattr(existing, key, value)
                skip_count += 1
                continue

            # 创建新单词记录
            word = WordBank(**word_data)
            session.add(word)
            success_count += 1

        except Exception as e:
            print(f"Error processing word: {e}", file=sys.stderr)
            skip_count += 1
            continue

    session.commit()
    return success_count, skip_count


def main():
    parser = argparse.ArgumentParser(
        description="导入单词数据到数据库",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog=__doc__,
    )
    parser.add_argument(
        "json_file",
        help="JSON文件路径",
    )
    parser.add_argument(
        "--tag",
        help="单词标签 (如 四级、六级、IELTS、托福、考研)",
        default=None,
    )
    parser.add_argument(
        "--difficulty",
        type=int,
        help="难度等级 (1=CET4, 2=CET6, 3=托福, 4=IELTS, 5=考研)",
        default=1,
    )
    parser.add_argument(
        "--dry-run",
        action="store_true",
        help="仅解析数据，不写入数据库",
    )

    args = parser.parse_args()

    # 验证JSON文件存在
    json_path = Path(args.json_file)
    if not json_path.exists():
        print(f"Error: File not found: {args.json_file}", file=sys.stderr)
        sys.exit(1)

    # 获取数据库URL
    database_url = os.getenv("DATABASE_URL")
    if not database_url:
        print("Error: DATABASE_URL environment variable not set", file=sys.stderr)
        sys.exit(1)

    print(f"Reading JSON file: {args.json_file}")
    words_data = parse_json_file(args.json_file)
    print(f"Found {len(words_data)} words in file")

    # 显示标签信息
    if args.tag:
        print(f"Tag filter: {args.tag}")
    print(f"Difficulty: {args.difficulty}")

    # 转换数据（预览）
    print("\nPreview first 3 words:")
    for i, word_item in enumerate(words_data[:3]):
        word_data = transform_word_data(word_item, args.tag, args.difficulty)
        if word_data:
            print(f"  {i + 1}. {word_data['word']} - {word_data['translation']}")

    if args.dry_run:
        print("\n[Dry run] No changes made to database")
        sys.exit(0)

    # 连接数据库
    engine = create_engine(database_url)
    SessionLocal = sessionmaker(bind=engine)
    session = SessionLocal()

    try:
        print("\nImporting words...")
        success_count, skip_count = import_words(
            session,
            words_data,
            args.tag,
            args.difficulty,
        )

        print(f"\nImport complete!")
        print(f"  Success: {success_count}")
        print(f"  Skipped: {skip_count}")

    except Exception as e:
        print(f"Error: {e}", file=sys.stderr)
        session.rollback()
        sys.exit(1)
    finally:
        session.close()


if __name__ == "__main__":
    main()
