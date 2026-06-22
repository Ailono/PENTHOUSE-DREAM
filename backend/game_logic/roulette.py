import random

EUROPEAN_NUMBERS = [0, 32, 15, 19, 4, 21, 2, 25, 17, 34, 6, 27, 13, 36, 11, 30, 8, 23, 10, 5, 24, 16, 33, 1, 20, 14, 31, 9, 22, 18, 29, 7, 28, 12, 35, 3, 26]

RED_NUMBERS = {1, 3, 5, 7, 9, 12, 14, 16, 18, 19, 21, 23, 25, 27, 30, 32, 34, 36}
BLACK_NUMBERS = {n for n in range(1, 37) if n not in RED_NUMBERS}

TABLE_ROWS = {
    0: [1, 4, 7, 10, 13, 16, 19, 22, 25, 28, 31, 34],
    1: [2, 5, 8, 11, 14, 17, 20, 23, 26, 29, 32, 35],
    2: [3, 6, 9, 12, 15, 18, 21, 24, 27, 30, 33, 36],
}

STREET_STARTS = [1, 4, 7, 10, 13, 16, 19, 22, 25, 28, 31, 34]

SIXLINE_STARTS = [1, 7, 13, 19, 25, 31]

BET_TYPES = {
    "straight": "Прямая ставка (одно число) - x36",
    "split": "Сплит (два числа) - x18",
    "street": "Стрит (три числа в ряду) - x12",
    "corner": "Корнер (четыре числа) - x9",
    "sixline": "Сикслайн (шесть чисел) - x6",
    "neighbors": "Соседи (число + 2 соседа) - x7",
    "red_black": "Красное/Чёрное - x2",
    "even_odd": "Чёт/Нечет - x2",
    "low_high": "1-18 / 19-36 - x2",
    "dozen": "Дюжина (1-12, 13-24, 25-36) - x3",
    "column": "Колонка - x3",
}


def get_color(number: int) -> str:
    if number == 0:
        return "green"
    return "red" if number in RED_NUMBERS else "black"


def get_dozen(number: int) -> int:
    if number == 0:
        return 0
    return (number - 1) // 12 + 1


def get_column(number: int) -> int:
    if number == 0:
        return 0
    return (number - 1) % 3 + 1


def get_row(number: int) -> int | None:
    for row_idx, nums in TABLE_ROWS.items():
        if number in nums:
            return row_idx
    return None


def get_street(number: int) -> int:
    if number == 0:
        return -1
    return (number - 1) // 3


def get_sixline(number: int) -> int:
    if number == 0:
        return -1
    return (number - 1) // 6


def get_wheel_neighbors(number: int, count: int = 2) -> list[int]:
    idx = EUROPEAN_NUMBERS.index(number)
    neighbors = []
    for offset in range(-count, count + 1):
        neighbors.append(EUROPEAN_NUMBERS[(idx + offset) % 37])
    return neighbors


def get_split_adjacent(number: int) -> list[int]:
    row = get_row(number)
    if row is None:
        return []
    row_nums = TABLE_ROWS[row]
    col = row_nums.index(number)
    adj = []
    if col > 0:
        adj.append(row_nums[col - 1])
    if col < len(row_nums) - 1:
        adj.append(row_nums[col + 1])
    for r in range(3):
        if r != row and number in TABLE_ROWS.get(r, []):
            c2 = TABLE_ROWS[r].index(number)
            adj.append(TABLE_ROWS[r][c2])
    return list(set(adj))


def spin(bet_type: str, bet_amount: int, bet_value: str = None) -> dict:
    number = random.choice(EUROPEAN_NUMBERS)
    color = get_color(number)
    win = False
    payout = 0

    if bet_type == "straight":
        if bet_value and number == int(bet_value):
            win = True
            payout = bet_amount * 36

    elif bet_type == "split":
        if bet_value:
            nums = [int(x.strip()) for x in bet_value.split(",")]
            if number in nums:
                win = True
                payout = bet_amount * 18

    elif bet_type == "street":
        if bet_value:
            start = int(bet_value)
            street_nums = TABLE_ROWS[get_row(start) or 0][get_street(start):get_street(start) + 3]
            if number in street_nums:
                win = True
                payout = bet_amount * 12

    elif bet_type == "corner":
        if bet_value:
            nums = [int(x.strip()) for x in bet_value.split(",")]
            if number in nums:
                win = True
                payout = bet_amount * 9

    elif bet_type == "sixline":
        if bet_value:
            start = int(bet_value)
            sixline_start = SIXLINE_STARTS.index(start) * 6 + 1
            sixline_nums = list(range(sixline_start, sixline_start + 6))
            if number in sixline_nums:
                win = True
                payout = bet_amount * 6

    elif bet_type == "neighbors":
        if bet_value:
            center = int(bet_value)
            neighbors = get_wheel_neighbors(center, 2)
            if number in neighbors:
                win = True
                payout = bet_amount * 7

    elif bet_type == "red_black":
        if bet_value and color == bet_value:
            win = True
            payout = bet_amount * 2

    elif bet_type == "even_odd":
        if number == 0:
            win = False
        elif bet_value == "even" and number % 2 == 0:
            win = True
            payout = bet_amount * 2
        elif bet_value == "odd" and number % 2 == 1:
            win = True
            payout = bet_amount * 2

    elif bet_type == "low_high":
        if number == 0:
            win = False
        elif bet_value == "low" and 1 <= number <= 18:
            win = True
            payout = bet_amount * 2
        elif bet_value == "high" and 19 <= number <= 36:
            win = True
            payout = bet_amount * 2

    elif bet_type == "dozen":
        dozen = get_dozen(number)
        if bet_value and dozen == int(bet_value):
            win = True
            payout = bet_amount * 3

    elif bet_type == "column":
        col = get_column(number)
        if bet_value and col == int(bet_value):
            win = True
            payout = bet_amount * 3

    return {
        "number": number,
        "color": color,
        "win": win,
        "payout": payout if win else 0,
        "bet_type": bet_type,
        "bet_amount": bet_amount,
    }
