import sys
def calc(a, b, op):
    if op == "add":
        return a + b
    if op == "sub":
        return a - b
    if op == "mul":
        return a * b
    if op == "div":
        return a / b
if __name__ == "__main__":
    print(calc(2, 3, "add"))
