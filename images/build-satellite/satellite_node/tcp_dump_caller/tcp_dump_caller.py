import os
import netifaces
from PyInquirer import prompt
import questions as qm


class TcpDumpCaller:
    def __init__(self):
        self.interface_list = []

    def load_all_interfaces(self):
        all_interfaces = netifaces.interfaces()
        for single_interface in all_interfaces:
            if single_interface != "eth0" and single_interface != "lo":
                self.interface_list.append(single_interface)

    def select_interface(self):
        interface_selection_question = qm.INTERFACE_SELECTION_QUESTION
        interface_selection_question[0]["choices"] = self.interface_list
        user_select_interface = prompt(interface_selection_question)["selected_interface"]
        user_select_storage = prompt(qm.STORAGE_SELECTION_QUESTION)["storage"]
        command = f"tcpdump -i {user_select_interface} -w {user_select_storage}"
        os.system(command)


if __name__ == "__main__":
    tcp_dump_caller = TcpDumpCaller()
    tcp_dump_caller.load_all_interfaces()
    tcp_dump_caller.select_interface()
