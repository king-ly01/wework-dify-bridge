"""验证器模块"""


def validate_bot_id_uniqueness(bots: list, owner: str, bot_id: str) -> tuple[bool, str]:
    """
    验证 bot_id 在指定 owner 下是否唯一
    
    Args:
        bots: 现有机器人列表
        owner: 配置人
        bot_id: 机器人 ID
    
    Returns:
        (是否有效, 错误信息)
    """
    for bot in bots:
        if bot.get("owner") == owner and bot.get("id") == bot_id:
            return False, f"您已经配置过名为 '{bot_id}' 的机器人了"
    return True, ""
