import time

from ground_station_decorator import signal_decorator as sdm


class Starter:
    def __init__(self):
        pass

    @sdm.signal_decorator
    def never_stop_until_signal(self):
        """
        主线程，只有当收到了 signal 的时候才会退出，否则反复睡觉
        :return:
        """
        while True:
            time.sleep(60)

    def main_logic(self):
        self.never_stop_until_signal()


if __name__ == "__main__":
    starter = Starter()
    starter.main_logic()
