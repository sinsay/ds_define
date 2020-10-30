import random

CHARS = ["a", "b", "c", "d", "e", "f", "g", "h", "i", "j", "k",
         "l", "m", "n", "o", "p", "q", "r", "s", "t", "u", "v",
         "w", "x", "y", "z", "1", "2", "3", "4", "5", "6", "7",
         "8", "9", "0"]

CHARS = CHARS + [c.upper() for c in CHARS]


def rand_str(min_len: int = 10, max_len: int = 64) -> str:
    """
    生成长度为 min_len 到 max_len 之间的随机字符串，默认只会使用 CHARS 定义的字母及数字
    """
    chars = [CHARS[random.randint(0, len(CHARS) - 1)] for _ in range(random.randint(min_len, max_len))]
    # chars = random.sample(CHARS, random.randint(10, 30))
    random.shuffle(chars)
    return "".join(chars)