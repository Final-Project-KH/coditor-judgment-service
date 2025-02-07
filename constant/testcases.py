TESTCASE_DICT = {
    "1": (
        (["3", "5"], "8"),
        (["0", "0"], "0"),
        (["-1", "5"], "4"),
        (["100", "200"], "300"),
        (["-10", "-20"], "-30"),
        (["1", "-5"], "-4"),
        (["999999", "-123123"], "876876"),
        (["-100", "50"], "-50"),
        (["1000", "255"], "1255"),
        (["-990", "-550"], "-1540"),
    ),

    "2": (
        (["10", "3"], "3 1"),
        (["100", "5"], "20 0"),
        (["-10", "3"], "-3 -1"),
        (["9", "2"], "4 1"),
        (["-9", "2"], "-4 -1"),
        (["7", "-2"], "-3 1"),
        (["-100", "-30"], "3 -10"),
        (["100000", "5000"], "20 0"),
        (["-100000", "5000"], "-20 0"),
        (["-1000", "-3"], "333 -1"),
    ),

    "3": (
        (["1", "-5"], "5"),
        (["-1", "5"], "5"),
        (["10", "-100"], "10"),
        (["-10", "100"], "10"),
        (["100", "200"], "-2"),
        (["-100", "-200"], "-2"),
        (["1", "1"], "-1"),
        (["-1", "-1"], "-1"),
        (["333", "-99999"], "300"),
        (["-85", "858585"], "10101"),
    ),

    "4": (
        (["1", "2"], "-1"),
        (["2", "1"], "1"),
        (["0", "0"], "0"),
        (["-1", "1"], "-1"),
        (["1", "-1"], "1"),
        (["100000", "100000"], "0"),
        (["-100000", "100000"], "-1"),
        (["100000", "-100000"], "1"),
        (["99999", "100000"], "-1"),
        (["100000", "99999"], "1"),
    ),

    "5": (
        (["1",], "0"),  # 최소값 테스트
        (["4",], "1"),  # 4로 나눠지지만 100으로 나눠지지 않음
        (["100",], "0"),  # 100으로 나눠지지만 400으로 나눠지지 않음
        (["400",], "1"),  # 400으로 나눠짐
        (["800",], "1"),  # 400으로 나눠짐
        (["1900",], "0"),  # 100으로 나눠지지만 400으로 나눠지지 않음
        (["2000",], "1"),  # 400으로 나눠짐
        (["2023",], "0"),  # 4로 나눠지지 않음
        (["2024",], "1"),  # 4로 나눠지지만 100으로 나눠지지 않음
        (["10000",], "1"),  # 최대값 테스트
    ),

    "6": (
        (["95"], "A"),
        (["85"], "B"),
        (["75"], "C"),
        (["65"], "D"),
        (["55"], "F"),
        (["100"], "A"),
        (["90"], "A"),
        (["80"], "B"),
        (["70"], "C"),
        (["60"], "D"),
    ),

    "7": (
        (["2"], "2 4 6 8 10 12 14 16 18"),
        (["3"], "3 6 9 12 15 18 21 24 27"),
        (["4"], "4 8 12 16 20 24 28 32 36"),
        (["5"], "5 10 15 20 25 30 35 40 45"),
        (["6"], "6 12 18 24 30 36 42 48 54"),
        (["7"], "7 14 21 28 35 42 49 56 63"),
        (["8"], "8 16 24 32 40 48 56 64 72"),
        (["9"], "9 18 27 36 45 54 63 72 81"),
        (["1"], "1 2 3 4 5 6 7 8 9")
    ),

    "8": (
        (["1"], "1"),
        (["2"], "3"),
        (["3"], "6"),
        (["4"], "10"),
        (["5"], "15"),
        (["10"], "55"),
        (["100"], "5050"),
        (["1000"], "500500"),
        (["10000"], "50005000"),
        (["9999"], "49995000"),
    ),

    "9": (
        (["1"], "*"),
        (["2"], "*\n**"),
        (["3"], "*\n**\n***"),
        (["4"], "*\n**\n***\n****"),
        (["5"], "*\n**\n***\n****\n*****"),
        (["6"], "*\n**\n***\n****\n*****\n******"),
        (["7"], "*\n**\n***\n****\n*****\n******\n*******"),
        (["8"], "*\n**\n***\n****\n*****\n******\n*******\n********"),
        (["9"], "*\n**\n***\n****\n*****\n******\n*******\n********\n*********"),
        (["10"], "*\n**\n***\n****\n*****\n******\n*******\n********\n*********\n**********"),
    ),

    "10": (
        (["5", "1 2 3 4 5"], "5"),
        (["5", "-1 -2 -3 -4 -5"], "-1"),
        (["5", "0 0 0 0 0"], "0"),
        (["5", "10000 20000 30000 40000 50000"], "50000"),
        (["5", "-10000 -20000 -30000 -40000 -50000"], "-10000"),
        (["5", "1 1 1 1 1"], "1"),
        (["5", "99999 99999 99999 99999 99999"], "99999"),
        (["5", "-99999 -99999 -99999 -99999 -99999"], "-99999"),
        (["5", "12345 54321 67890 98765 43210"], "98765"),
        (["5", "-12345 -54321 -67890 -98765 -43210"], "-12345"),
    ),

    "11": (
        (["5", "1 2 3 4 5"], "5 4 3 2 1"),
        (["5", "-1 -2 -3 -4 -5"], "-5 -4 -3 -2 -1"),
        (["5", "0 0 0 0 0"], "0 0 0 0 0"),
        (["5", "10000 20000 30000 40000 50000"], "50000 40000 30000 20000 10000"),
        (["5", "-10000 -20000 -30000 -40000 -50000"], "-50000 -40000 -30000 -20000 -10000"),
        (["5", "1 1 1 1 1"], "1 1 1 1 1"),
        (["5", "99999 99999 99999 99999 99999"], "99999 99999 99999 99999 99999"),
        (["5", "-99999 -99999 -99999 -99999 -99999"], "-99999 -99999 -99999 -99999 -99999"),
        (["5", "12345 54321 67890 98765 43210"], "43210 98765 67890 54321 12345"),
        (["5", "-12345 -54321 -67890 -98765 -43210"], "-43210 -98765 -67890 -54321 -12345"),
    ),

    "12": (
        (["2", "2", "1 2", "3 4"], "10"),
        (["3", "3", "1 2 3", "4 5 6", "7 8 9"], "45"),
        (["1", "1", "1"], "1"),
        (["2", "2", "-1 -2", "-3 -4"], "-10"),
        (["3", "3", "-1 -2 -3", "-4 -5 -6", "-7 -8 -9"], "-45"),
        (["2", "2", "0 0", "0 0"], "0"),
        (["3", "3", "10000 20000 30000", "40000 50000 60000", "70000 80000 90000"], "450000"),
        (["3", "3", "-10000 -20000 -30000", "-40000 -50000 -60000", "-70000 -80000 -90000"], "-450000"),
        (["2", "2", "12345 54321", "67890 98765"], "233321"),
        (["2", "2", "-12345 -54321", "-67890 -98765"], "-233321"),
    ),

    "13": (
        (["Hello"], "5"),
        (["Python"], "6"),
        ([""], "0"),
        (["1234567890"], "10"),
        (["abcdefghijklmnopqrstuvwxyz"], "26"),
        (["ABCDEFGHIJKLMNOPQRSTUVWXYZ"], "26"),
        (["!@#$%^&*()"], "10"),
        (["Hello, World!"], "13"),
        (["123 456 789"], "11"),
        (["Python is fun"], "13"),
    ),

    "14": (
        (["Hello World", "o"], "2"),
        (["Python Programming", "P"], "2"),
        (["", "a"], "0"),
        (["1234567890", "1"], "1"),
        (["abcdefghijklmnopqrstuvwxyz", "z"], "1"),
        (["ABCDEFGHIJKLMNOPQRSTUVWXYZ", "A"], "1"),
        (["!@#$%^&*()", "!"], "1"),
        (["Hello, World!", "l"], "3"),
        (["123 456 789", " "], "2"),
        (["Python is fun", "n"], "2"),
    ),

    "15": (
        (["Hello World"], "hELLO wORLD"),
        (["Python Programming"], "pYTHON pROGRAMMING"),
        (["1234567890"], "1234567890"),
        (["abcdefghijklmnopqrstuvwxyz"], "ABCDEFGHIJKLMNOPQRSTUVWXYZ"),
        (["ABCDEFGHIJKLMNOPQRSTUVWXYZ"], "abcdefghijklmnopqrstuvwxyz"),
        (["!@#$%^&*()"], "!@#$%^&*()"),
        (["Hello, World!"], "hELLO, wORLD!"),
        (["123 456 789"], "123 456 789"),
        (["Python is fun"], "pYTHON IS FUN"),
        (["aBcDeFgHiJkLmNoPqRsTuVwXyZ"], "AbCdEfGhIjKlMnOpQrStUvWxYz"),
    ),

    "16": (
        (["1"], "true"),  # 단일 자리 암스트롱 수 (최소값)
        (["9"], "true"),  # 단일 자리 암스트롱 수
        (["10"], "false"),  # 두 자리 숫자 (암스트롱 수 아님)
        (["153"], "true"),  # 세 자리 암스트롱 수
        (["9474"], "true"),  # 네 자리 암스트롱 수
        (["9475"], "false"),  # 네 자리 숫자 (암스트롱 수 아님)
        (["370"], "true"),  # 세 자리 암스트롱 수
        (["9476"], "false"),  # 네 자리 숫자 (암스트롱 수 아님)
        (["548834"], "true"),  # 여섯 자리 암스트롱 수
        (["999999"], "false")  # 여섯 자리 숫자 (암스트롱 수 아님, 최대값 테스트)
    ),
    "17": (
        (["0", "0"], "10"),  # 중심 원
        (["1", "0"], "10"),  # 중심 원 경계
        (["3", "4"], "5"),  # 중간 원
        (["5", "0"], "5"),  # 중간 원 경계
        (["6", "8"], "1"),  # 외곽 원
        (["-6", "-8"], "1"),  # 외곽 원
        (["10", "0"], "1"),  # 외곽 원 경계
        (["9", "9"], "0"),  # 표적 바깥
        (["-10", "-10"], "0"),  # 표적 바깥
        (["4.33", "3.25"], "1")  # 중간 원 내부
    )
}

TESTCASE_TIMEOUT_LIMIT = {
    "1": 5,
    "2": 5,
    "3": 5,
    "4": 5,
    "5": 5,
    "6": 5,
    "7": 5,
    "8": 5,
    "9": 5,
    "10": 5,
    "11": 5,
    "12": 5,
    "13": 5,
    "14": 5,
    "15": 5,
    "16": 5,
    "17": 5
}