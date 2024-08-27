import functools
import logging
import multiprocessing
import sys
from io import StringIO
from typing import Dict, Optional


logger = logging.getLogger(__name__)


@functools.lru_cache(maxsize=None)
def warn_once() -> None:
    """Warn once about the dangers of PythonREPL."""
    logger.warning("Python REPL can execute arbitrary code. Use with caution.")


class PythonREPL:
    """Simulates a standalone Python REPL."""

    def __init__(self):
        self.globals = {}
        self.locals = {}

    @classmethod
    def worker(
            cls,
            command: str,
            globals: Dict,
            locals: Dict,
            queue: multiprocessing.Queue,
    ) -> None:
        old_stdout = sys.stdout
        sys.stdout = mystdout = StringIO()
        try:
            exec(command, globals, locals)
            sys.stdout = old_stdout
            queue.put(mystdout.getvalue())
        except Exception as e:
            sys.stdout = old_stdout
            queue.put(repr(e))

    def run(self, code: str, timeout: Optional[int] = None) -> str:
        """Execute a Python code with own globals/locals and return anything printed to stdout.
        Timeout after the specified number of seconds.

        Args:
            code: A string containing the Python code to be executed.

        Returns:
            The output of the executed code as a string. If an exception occurs,
            the exception message is returned.
        """

        # Warn against dangers of PythonREPL
        warn_once()

        queue: multiprocessing.Queue = multiprocessing.Queue()

        # Only use multiprocessing if we are enforcing a timeout
        if timeout is not None:
            # create a Process
            p = multiprocessing.Process(
                target=self.worker, args=(code, self.globals, self.locals, queue)
            )

            # start it
            p.start()

            # wait for the process to finish or kill it after timeout seconds
            p.join(timeout)

            if p.is_alive():
                p.terminate()
                return "Execution timed out"
        else:
            self.worker(code, self.globals, self.locals, queue)
        # get the result from the worker function
        return queue.get()


def main():
    # Initialize PythonREPL instance
    repl = PythonREPL()

    # Execute a simple print statement
    output = repl.run("print('Hello, world!')")
    print(f"Output: {output}")  # Should print: "Hello, world!\n"

    # Execute a multi-line code block
    code = """
x = 10
print(2 * x)
    """
    output = repl.run(code)
    print(f"Output: {output}")  # Should print: "20\n"

    # Use the globals and locals to maintain state between calls
    repl.run("x = 10")
    repl.run("x += 5")
    output = repl.run("print(x)")
    print(f"Output: {output}")  # Should print: "15\n"

    # Catch, handle and display an exception
    output = repl.run("1 / 0")
    print(f"Output: {output}")  # Should print: "division by zero"

    # Use multiprocessing and timeout
    code = """
import time
time.sleep(5)
print('Finished sleeping')
    """
    output = repl.run(code, timeout=2)
    print(f"Output: {output}")  # Should print: "Execution timed out"


if __name__ == "__main__":
    main()
