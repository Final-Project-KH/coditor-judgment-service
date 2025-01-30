"""
문제 1: 두 정수의 덧셈

1. 설명: 두 정수가 줄바꿈 문자(\n)로 구분되어 입력으로 주어집니다. 두 정수의 합을 출력하는 코드를 작성하세요.

2. input 정의역: -100,000 <= x, y <= 100,000

3. 실행 환경: memory: 128mb, 실행 시간 5초 이내

4. 입력, 출력 정답 예시
입력    |   출력
5, 7   |   12
0, -1  |  -1

[예시 답안]
import java.util.Scanner;

public class Main {
    public static void main(String[] args) {
        Scanner sc = new Scanner(System.in);
        int number1 = Integer.parseInt(sc.nextLine());
        int number2 = Integer.parseInt(sc.nextLine());
        System.out.print(number1 + number2);
    }
}

-----------------------------------------------------------------------------------------------------

문제 2: 문자열 뒤집기

1. 설명: 주어진 문자열을 뒤집는 프로그램을 작성하세요.
- 문자열 뒤집기는 문자열을 오른쪽에서 왼쪽으로 읽는 작업을 의미합니다.
- 이는 다양한 분야에서 중요한 작업으로, 예를 들어 생물정보학에서는 DNA나 RNA 서열을 뒤집어 분석하거나, 회문(palindrome)을 판별하는 데 사용됩니다.

2. input 길이 정의역: 1 <= length of string <= 100

3. 실행 환경: memory: 128mb, 실행 시간 5초 이내

4. 입력, 출력 정답 예시
입력           |   출력
"stressed"     |   "desserts"
"strops"       |   "sports"
"racecar"      |   "racecar"
"hello"        |   "olleh"
"12345"        |   "54321"

[예시 답안]
import java.util.Scanner;

public class Main {
    public static void main(String[] args) {
        Scanner sc = new Scanner(System.in);
        String input = sc.nextLine();
        System.out.println(reverseString(input));
    }

    public static String reverseString(String input) {
        StringBuilder reversed = new StringBuilder(input);
        return reversed.reverse().toString();
    }
}

-----------------------------------------------------------------------------------------------------

문제 3: 윤년 계산

1. 설명: 그레고리력을 기준으로 주어진 연도가 윤년인지 판별하는 코드를을 작성하세요. 윤년은 다음 조건을 만족합니다.
    - 연도가 4로 나누어 떨어지면 윤년입니다.
    - 하지만 100으로 나누어 떨어지는 경우 윤년이 아닙니다.
    - 단, 400으로 나누어 떨어지는 경우 다시 윤년이 됩니다.

2. input 정의역: 1 <= year <= 10,000

3. 실행 환경: memory: 128mb, 실행 시간 5초 이내

4. 입력, 출력 정답 예시
입력    |    출력
1997   |   false
1900   |   false
2000   |   true
2024   |   true

[예시 답안]
import java.common.Scanner;

public class Main {
    public static void main(String[] args) {
        Scanner sc = new Scanner(System.in);
        int year = Integer.parseInt(sc.nextLine());
        System.out.print(isLeapYear(year));
    }

    public static boolean isLeapYear(int year) {
        if (year % 4 == 0) {
            if (year % 100 == 0) {
                return year % 400 == 0;
            } else {
                return true;
            }
        } else {
            return false;
        }
    }
}

-----------------------------------------------------------------------------------------------------

문제 4: 암스트롱 수

1. 설명: 주어진 양의 정수의 암스트롱 수 여부를 출력하는 코드를 작성하세요.
암스트롱 수(Armstrong number)는 각 자리 숫자를 모두 n제곱(여기서 n은 자릿수)한 합이 원래 수와 같은 수를 말합니다.
- 예를 들어:
 - 9는 암스트롱 수입니다. (9 = 9^1)
 - 10은 암스트롱 수가 아닙니다. (10 != 1^2 + 0^2)
 - 153은 암스트롱 수입니다. (153 = 1^3 + 5^3 + 3^3 = 1 + 125 + 27 = 153)

2. input 정의역: 1 <= x <= 1,000,000

3. 실행 환경: memory: 128mb, 실행 시간 5초 이내

4. 입력, 출력 정답 예시
입력    |   출력
9       |   true
10      |   false
153     |   true
154     |   false
9474    |   true
9475    |   false

[예시 답안]
import java.common.Scanner;

public class Main {
    public static void main(String[] args) {
        Scanner sc = new Scanner(System.in);
        int number = Integer.parseInt(sc.nextLine());
        System.out.println(isArmstrong(number));
    }

    public static boolean isArmstrong(int number) {
        String numStr = Integer.toString(number);
        int length = numStr.length();
        int sum = 0;

        for (int i = 0; i < length; i++) {
            int digit = Character.getNumericValue(numStr.charAt(i));
            sum += Math.pow(digit, length);
        }

        return sum == number;
    }
}

-----------------------------------------------------------------------------------------------------

문제 5: 다트 게임 점수 계산

1. 설명: 다트 게임에서 주어진 좌표(x, y)를 기준으로 다트가 어디에 맞았는지 확인하고, 점수를 계산하세요.
점수는 다음과 같은 규칙에 따라 부여됩니다:
   - 다트가 표적 바깥에 떨어지면: **0점**
   - 다트가 외곽 원(반지름 10) 안에 떨어지면: **1점**
   - 다트가 중간 원(반지름 5) 안에 떨어지면: **5점**
   - 다트가 중심 원(반지름 1) 안에 떨어지면: **10점**

   **원의 중심은 (0, 0)**이며, 주어진 좌표(x, y)를 기준으로 유클리드 거리(\( \sqrt{x^2 + y^2} \))를 계산하여 점수를 판별합니다.

2. input 정의역: −10 <= x, y <= 10, (단, x와 y는 소수점 2번째 자리까지만 주어짐)

3. 실행 환경: memory: 128mb, 실행 시간 5초 이내

4. 입력, 출력 정답 예시
입력           |   출력
(0, 0)         |   10
(2, 2)         |   5
(6, 8)         |   1
(12, 0)        |   0
(5, 0)         |   5

[예시 답안]
import java.common.Scanner;

public class Main {
    public static void main(String[] args) {
        Scanner sc = new Scanner(System.in);

        // x, y 좌표 입력
        double x = sc.nextDouble();
        double y = sc.nextDouble();

        System.out.println(getScore(x, y));
    }

    public static int getScore(double x, double y) {
        double distance = Math.sqrt(x * x + y * y);

        if (distance > 10) {
            return 0;  // 표적 바깥
        } else if (distance > 5) {
            return 1;  // 외곽 원
        } else if (distance > 1) {
            return 5;  // 중간 원
        } else {
            return 10; // 중심 원
        }
    }
}
"""

TESTCASE_TIMEOUT_LIMIT = {
    "1": 5,
    "2": 5,
}

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
        (["a"], "a"),  # 최소값 (1자리 문자열)
        (["ab"], "ba"),  # 2자리 문자열
        (["hello"], "olleh"),  # 5자리 문자열
        (["abcdefghij"], "jihgfedcba"),  # 10자리 문자열
        (["abcdefghijklmnopqrstuvwxyz"], "zyxwvutsrqponmlkjihgfedcba"),  # 26자리 문자열 (알파벳 전체)
        (["123456789012345678901234567890"], "098765432109876543210987654321"),  # 30자리 숫자 문자열
        (["A quick brown fox jumps over the lazy dog"], "god yzal eht revo spmuj xof nworb kciuq A"),  # 43자리 공백 포함
        (["x" * 50], "x" * 50),  # 50자리 동일 문자 반복
        (["racecar"], "racecar"),  # 회문 문자열 (뒤집어도 동일)
        (["abcdefghij" * 10], "jihgfedcba" * 10)  # 최대값 (100자리 문자열)
    ),
    "3": (
        (["1",], "false"),  # 최소값 테스트
        (["4",], "true"),  # 4로 나눠지지만 100으로 나눠지지 않음
        (["100",], "false"),  # 100으로 나눠지지만 400으로 나눠지지 않음
        (["400",], "true"),  # 400으로 나눠짐
        (["800",], "true"),  # 400으로 나눠짐
        (["1900",], "false"),  # 100으로 나눠지지만 400으로 나눠지지 않음
        (["2000",], "true"),  # 400으로 나눠짐
        (["2023",], "false"),  # 4로 나눠지지 않음
        (["2024",], "true"),  # 4로 나눠지지만 100으로 나눠지지 않음
        (["10000",], "false"),  # 최대값 테스트
    ),
    "4": (
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
    "5": (
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
