"""会话标题自动生成模块。"""


def generate_title_from_message(message: str, subject: str) -> str:
    """从第一条用户消息生成会话标题（规则版，无 LLM）。"""
    subject_names = {
        "calculus": "\u9ad8\u6570",
        "linear_algebra": "\u7ebf\u4ee3",
        "probability": "\u6982\u7387\u8bba",
    }
    subject_zh = subject_names.get(subject, "\u6570\u5b66")

    # 提取关键词
    keywords = []
    concept_hints = {
        "\u79ef\u5206": "\u79ef\u5206",
        "\u5bfc\u6570": "\u5bfc\u6570",
        "\u6781\u9650": "\u6781\u9650",
        "\u884c\u5217\u5f0f": "\u884c\u5217\u5f0f",
        "\u77e9\u9635": "\u77e9\u9635",
        "\u7279\u5f81": "\u7279\u5f81\u503c",
        "\u6982\u7387": "\u6982\u7387",
        "\u5206\u5e03": "\u5206\u5e03",
        "\u6d1b\u5fc5\u8fbe": "\u6d1b\u5fc5\u8fbe",
        "\u94fe\u5f0f": "\u94fe\u5f0f\u6cd5\u5219",
        "\u6cf0\u52d2": "\u6cf0\u52d2\u5c55\u5f00",
        "\u8d1d\u53f6\u65af": "\u8d1d\u53f6\u65af",
        "\u65b9\u5dee": "\u65b9\u5dee",
        "\u671f\u671b": "\u671f\u671b",
    }
    for key, label in concept_hints.items():
        if key in message:
            keywords.append(label)
            if len(keywords) >= 2:
                break

    if keywords:
        title = f"{subject_zh}-{'/'.join(keywords)}"
    else:
        # 取消息前 10 个字符
        clean = message.replace("$", "").replace("\\", "").strip()
        title = f"{subject_zh}-{clean[:10]}"

    return title[:15]


def generate_title_prompt(messages: list[str]) -> str:
    """生成让 LLM 起标题的 prompt。"""
    combined = "\n".join(messages[:2])
    return (
        f"\u8bf7\u4e3a\u4ee5\u4e0b\u6570\u5b66\u8f85\u5bfc\u4f1a\u8bdd\u751f\u621015\u5b57\u4ee5\u5185\u7684\u4e2d\u6587\u6807\u9898\uff0c"
        f"\u53ea\u8f93\u51fa\u6807\u9898\u672c\u8eab\uff1a\n\n{combined}"
    )
