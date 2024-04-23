from datetime import datetime


class TleGenerator:
    @staticmethod
    def get_year_day(now_time: datetime) -> (int, float):
        year = now_time.year
        day = float(now_time.microsecond)
        day /= 1000
        day += now_time.second
        day /= 60
        day += now_time.minute
        day /= 60
        day += now_time.hour
        day /= 24
        day += (now_time - datetime(year, 1, 1)).days

        return year % 100, day

    @staticmethod
    def str_checksum(line: str) -> int:
        sum_num = 0
        for c in line:
            if c.isdigit():
                sum_num += int(c)
            elif c == '-':
                sum_num += 1
        return sum_num % 10

    def generate_tle(self, orbit_num: int, orbit_satellite_num: int, latitude, longitude, delta, period) -> list:
        tles = []
        freq = 1 / period
        line_1 = "1 00000U 23666A   %02d%012.8f  .00000000  00000-0 00000000 0 0000"
        line_2 = "2 00000  90.0000 %08.4f 0000011   0.0000 %8.4f %11.8f00000"
        year2, day = TleGenerator.get_year_day(datetime.now())
        for i in range(orbit_num):
            start_latitude = latitude + delta * i
            start_longitude = longitude + 180 * i / orbit_num
            for j in range(orbit_satellite_num):
                this_latitude = start_latitude + 360 * j / orbit_satellite_num
                this_line_1 = line_1 % (year2, day)
                this_line_2 = line_2 % (start_longitude, this_latitude, freq)
                tles.append((this_line_1 + str(TleGenerator.str_checksum(this_line_1)), this_line_2 + str(TleGenerator.str_checksum(this_line_2))))
        return tles


if __name__ == "__main__":
    tle_generator = TleGenerator()
    tles = tle_generator.generate_tle(6, 11, 0, 0, 5, 1 / 14.4)
    for single_tle in tles:
        print(single_tle)
