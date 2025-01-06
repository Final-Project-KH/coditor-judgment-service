"""
문제 1: 두 정수의 덧셈

[정답 예시]
public class Main {
    public static void main(String[] args) {
        java.util.Scanner sc = new java.util.Scanner(System.in);
        int number1 = Integer.parseInt(sc.nextLine());
        int number2 = Integer.parseInt(sc.nextLine());

        Solution solution = new Solution();
        int result = solution.solve(number1, number2);
        System.out.println(result);
    }
}

class Solution {
    public int solve(int number1, int number2) {
        return number1 + number2;
    }
}
"""

java_test_cases = {
    "1": [
        (["3", "5"], 8),
        (["0", "0"], 0),
        (["-1", "5"], 4),
        (["100", "200"], 300),
        (["-10", "-20"], -30),
        (["1", "-5"], -4),
        (["999999", "-123123"], 876876),
        (["-100", "50"], -50),
        (["1000", "255"], 1255),
        (["-990", "-550"], -1540),
    ]
}


"""
문제 2: 
"""