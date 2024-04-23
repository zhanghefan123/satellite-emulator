def get_lir_total_delay():
    file_path = "/var/log/kern.log"
    nano_seconds_of_lir = 0
    nano_seconds_of_ip = 0
    lines_lir = 0
    lines_ip = 0
    available_lines_of_lir = 0
    available_lines_of_ip = 0
    with open(file_path) as f:
        all_lines = f.readlines()
        for line in all_lines:
            if line.find("lir rcv take") != -1:
                lines_lir += 1
                if lines_lir % 4 == 0:
                    continue
                left = line.find("lir rcv take") + len("lir rcv take")
                right = line.find("nano")
                nano_seconds = int(line[left:right].strip())
                nano_seconds_of_lir += nano_seconds
                available_lines_of_lir += 1
            elif line.find("ip rcv take") != -1:
                lines_ip += 1
                if lines_ip % 4 == 0:
                    continue
                left = line.find("ip rcv take") + len("ip rcv take")
                right = line.find("nano")
                nano_seconds = int(line[left:right].strip())
                nano_seconds_of_ip += nano_seconds
                available_lines_of_ip += 1
    print(f"lines lir: {lines_lir}, lines ip: {lines_ip}")
    print(f"micro seconds of lir: {nano_seconds_of_lir / 1000 / available_lines_of_lir}")
    print(f"micro seconds of ip: {nano_seconds_of_ip / 1000 / available_lines_of_ip}")


if __name__ == "__main__":
    get_lir_total_delay()

# lines lir: 408, lines ip: 404
# micro seconds of lir: 4.1629346405228755
# micro seconds of ip: 8.69679207920792