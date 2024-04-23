
class Test:
    def __init__(self, test):
        self.test = test

    def print(self):
        print(self.test)


if __name__ == "__main__":
    test1 = []
    test_tmp = Test(test1)
    test1.append(3)
    test_tmp.print()
