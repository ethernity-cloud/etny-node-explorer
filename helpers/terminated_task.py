from operator import rshift
import os, sys, asyncio, time, signal

class TerminatedTask:

    def __init__(self, cmd = '', callback = None, callback_on_complete = None, time_limit = 0) -> None:
        self._cmd = cmd
        self._callback = callback
        self.callback_on_complete = callback_on_complete
        self._time_limit = time_limit

        self.__isTerminated = False
        self.__isCompleted = False
        self.__hasError = False
        self.__inlineProc = None

        self.__result = None
        
    def run(self):
        asyncio.run(self.task_to_complete())
        return self.__result

    def kill_process(self) -> None:
        try:
            os.killpg(self.__inlineProc.pid, signal.SIGTERM)
            os.killpg(os.getpgid(self.__inlineProc.pid), signal.SIGCHLD)
        except ProcessLookupError as e:
            print(e)
        self.__inlineProc.kill()
        self.__isTerminated = True

    async def until_finished(self) -> None:
        t = time.time()
        while True:
            if self.__isCompleted or self.__hasError: 
                if self.callback_on_complete:
                    self.callback_on_complete()
                break
            if self._time_limit and int(time.time() - t) >= self._time_limit:
                return self.kill_process()
            sys.stdout.write('-')
            sys.stdout.flush()
            await asyncio.sleep(1)

    async def command(self) -> None:
        try:
            self.__inlineProc = await asyncio.create_subprocess_shell(self._cmd, stdout=asyncio.subprocess.PIPE, stderr=asyncio.subprocess.PIPE, shell=True, preexec_fn=os.setsid)
            stdout, stderr = await self.__inlineProc.communicate()
            if self.__isTerminated:return
            result = dict(
                stdout = stdout.decode() if stdout else '', 
                stderr = stderr.decode() if stderr else ''
            )
            self.__isCompleted = True
            if self._callback:
                self._callback(**result)
            self.__result = result
        except:
            self.__hasError = True

    async def task_to_complete(self) -> None:
        await asyncio.gather(
            self.command(),
            self.until_finished()
        )
        
    @property
    def isTerminated(self) -> bool:
        return self.__isTerminated

    @property
    def isCompleted(self) -> bool:
        return self.__isCompleted

    @property
    def hasError(self) -> bool:
        return self.__hasError

    @property
    def inlineProc(self) -> object:
        return self.__inlineProc

if __name__ == '__main__':
    def callback(stdout, stderr):
        if stdout:
            print(f'[stdout]\n{stdout}')
        if stderr:
            print(f'[stderr]\n{stderr}')

    #cmd = f'python3 {os.getcwd()}/check.py 3'
    cmd = f'sleep 1; echo "just something here"'

    t = TerminatedTask(
        cmd=cmd,
        callback=callback,
        time_limit=3
    )
    result = t.run()

    # print(f'[{cmd} exited with {t.inlineProc.returncode}]')
    print('isTreminated = ', t.isTerminated)
    print('isCompleted = ', t.isCompleted)
    print('hasError = ', t.hasError)


    print('result = ', result)