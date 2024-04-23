from typing import List, Tuple
from concurrent.futures import ThreadPoolExecutor
from concurrent.futures import as_completed
import os
import tqdm
import time


class MultithreadExecutor:

    def __init__(self, max_workers=10):
        self.max_workers = max_workers

    def execute_with_multiple_thread(self, task_list: List, args_list: List[Tuple], description: str, enable_tqdm=True):
        """
        进行任务的执行
        :param description:
        :param task_list: 任务列表
        :param args_list: 每一个任务的参数列表
        :param enable_tqdm: 使能 tqdm
        :return:
        """
        with ThreadPoolExecutor(max_workers=self.max_workers) as executor:
            # submit tasks
            all_tasks = [executor.submit(task_list[index], *(args_list[index])) for index in range(len(task_list))]
            # 判断是否需要 tqdm
            if enable_tqdm:
                bar_format = '{desc}{percentage:3.0f}%|{bar}|{n_fmt}/{total_fmt}'
                with tqdm.tqdm(total=len(all_tasks), colour="green", ncols=97, postfix="", bar_format=bar_format) as pbar:
                    pbar.set_description(description)
                    for future in as_completed(all_tasks):
                        pbar.update(1)  # finished single task
            else:
                # start_time = time.time()
                for future in as_completed(all_tasks):
                    pass
                # time_elapsed = time.time() - start_time
                # print(f"time elapsed: {time_elapsed}")



class CommandExecutor:
    @staticmethod
    def execute_command(command):
        os.system(command)


if __name__ == "__main__":
    multithread_executor = MultithreadExecutor(max_workers=2)
    command_list = [CommandExecutor.execute_command, CommandExecutor.execute_command]
    args_list_tmp = [("ip addr", ), ("ip addr", )]
    multithread_executor.execute_with_multiple_thread(command_list, args_list_tmp, "hello")
