import asyncio
import subprocess


class CommandParallelExecutor:
    @classmethod
    def execute(cls, command="echo 'hello'"):
        try:
            subprocess.run(command, shell=True)
            return 0
        except subprocess.CalledProcessError as e:
            print(f"命令执行失败，错误信息: {e}")
            return -1

    @classmethod
    async def async_execute(cls, command):
        try:
            process = await asyncio.create_subprocess_shell(command,
                                                            stdout=asyncio.subprocess.PIPE,
                                                            stderr=asyncio.subprocess.PIPE)
            output, _ = await process.communicate()
            print(output)
            return ""
        except subprocess.CalledProcessError as e:
            print(f"命令执行失败，错误信息: {e}")
            return -1


if __name__ == "__main__":
    CommandParallelExecutor.execute()
