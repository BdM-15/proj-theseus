"""
RAG-Anything MinerU Error Detail Patch

Problem:
    raganything.parser.MineruParser._run_mineru_command truncates MinerU CLI
    stderr to only the first line containing the word "error". MinerU's CLI
    often emits the useful cause on following lines, e.g.:

        Error: 1 task(s) failed while processing documents:
        - task#0 (foo): actual underlying reason

    The current wrapper drops the second line, so application logs only show
    the generic banner and hide the actionable failure reason.

Fix:
    Monkey-patch _run_mineru_command to retain all stderr lines when the MinerU
    subprocess exits non-zero, while keeping the existing logging behavior.

When to remove:
    When raganything preserves full MinerU stderr details upstream.
"""

import logging
import os
import subprocess
from pathlib import Path
from typing import Optional, Union

logger = logging.getLogger(__name__)

_PATCHED = False


def apply_patch():
    """Monkey-patch MineruParser._run_mineru_command to preserve stderr details."""
    global _PATCHED
    if _PATCHED:
        return

    from raganything.parser import MineruParser, MineruExecutionError

    @classmethod
    def _patched_run_mineru_command(
        cls,
        input_path: Union[str, Path],
        output_dir: Union[str, Path],
        method: str = "auto",
        lang: Optional[str] = None,
        backend: Optional[str] = None,
        start_page: Optional[int] = None,
        end_page: Optional[int] = None,
        formula: bool = True,
        table: bool = True,
        device: Optional[str] = None,
        source: Optional[str] = None,
        vlm_url: Optional[str] = None,
        **kwargs,
    ) -> None:
        cmd = [
            "mineru",
            "-p",
            str(input_path),
            "-o",
            str(output_dir),
            "-m",
            method,
        ]

        if backend:
            cmd.extend(["-b", backend])
        if lang:
            cmd.extend(["-l", lang])
        if start_page is not None:
            cmd.extend(["-s", str(start_page)])
        if end_page is not None:
            cmd.extend(["-e", str(end_page)])
        if not formula:
            cmd.extend(["-f", "false"])
        if not table:
            cmd.extend(["-t", "false"])
        if vlm_url:
            cmd.extend(["-u", vlm_url])

        output_lines: list[str] = []
        stderr_lines: list[str] = []
        flagged_error_lines: list[str] = []

        custom_env = kwargs.pop("env", None)
        if custom_env is not None:
            if not isinstance(custom_env, dict):
                raise TypeError(
                    f"env must be a dictionary, got {type(custom_env).__name__}"
                )
            for key, value in custom_env.items():
                if not isinstance(key, str) or not isinstance(value, str):
                    raise TypeError("env keys and values must be strings")

        if kwargs:
            unsupported = ", ".join(kwargs.keys())
            raise TypeError(
                f"MineruParser._run_mineru_command received unexpected keyword argument(s): {unsupported}"
            )

        try:
            import platform
            import threading
            import time
            from queue import Empty, Queue

            cls.logger.info(f"Executing mineru command: {' '.join(cmd)}")

            env = None
            if custom_env:
                env = os.environ.copy()
                env.update(custom_env)

            subprocess_kwargs = {
                "stdout": subprocess.PIPE,
                "stderr": subprocess.PIPE,
                "text": True,
                "encoding": "utf-8",
                "errors": "ignore",
                "bufsize": 1,
                "env": env,
            }

            if platform.system() == "Windows":
                subprocess_kwargs["creationflags"] = subprocess.CREATE_NO_WINDOW

            def enqueue_output(pipe, queue, prefix):
                try:
                    for line in iter(pipe.readline, ""):
                        if line.strip():
                            queue.put((prefix, line.strip()))
                    pipe.close()
                except Exception as exc:
                    queue.put((prefix, f"Error reading {prefix}: {exc}"))

            process = subprocess.Popen(cmd, **subprocess_kwargs)

            stdout_queue = Queue()
            stderr_queue = Queue()

            stdout_thread = threading.Thread(
                target=enqueue_output, args=(process.stdout, stdout_queue, "STDOUT")
            )
            stderr_thread = threading.Thread(
                target=enqueue_output, args=(process.stderr, stderr_queue, "STDERR")
            )

            stdout_thread.daemon = True
            stderr_thread.daemon = True
            stdout_thread.start()
            stderr_thread.start()

            while process.poll() is None:
                try:
                    while True:
                        _prefix, line = stdout_queue.get_nowait()
                        output_lines.append(line)
                        cls.logger.info(f"[MinerU] {line}")
                except Empty:
                    pass

                try:
                    while True:
                        _prefix, line = stderr_queue.get_nowait()
                        stderr_lines.append(line)
                        line_lower = line.lower()
                        if "warning" in line_lower:
                            cls.logger.warning(f"[MinerU] {line}")
                        elif "error" in line_lower:
                            cls.logger.error(f"[MinerU] {line}")
                            flagged_error_lines.append(line)
                        else:
                            cls.logger.info(f"[MinerU] {line}")
                except Empty:
                    pass

                time.sleep(0.1)

            try:
                while True:
                    _prefix, line = stdout_queue.get_nowait()
                    output_lines.append(line)
                    cls.logger.info(f"[MinerU] {line}")
            except Empty:
                pass

            try:
                while True:
                    _prefix, line = stderr_queue.get_nowait()
                    stderr_lines.append(line)
                    line_lower = line.lower()
                    if "warning" in line_lower:
                        cls.logger.warning(f"[MinerU] {line}")
                    elif "error" in line_lower:
                        cls.logger.error(f"[MinerU] {line}")
                        flagged_error_lines.append(line)
                    else:
                        cls.logger.info(f"[MinerU] {line}")
            except Empty:
                pass

            return_code = process.wait()
            stdout_thread.join(timeout=5)
            stderr_thread.join(timeout=5)

            if return_code != 0 or flagged_error_lines:
                cls.logger.info("[MinerU] Command executed failed")
                detailed_lines = stderr_lines or flagged_error_lines or ["MinerU command failed without stderr output"]
                raise MineruExecutionError(return_code, detailed_lines)

            cls.logger.info("[MinerU] Command executed successfully")

        except MineruExecutionError:
            raise
        except subprocess.CalledProcessError as exc:
            cls.logger.error(f"Error running mineru subprocess command: {exc}")
            cls.logger.error(f"Command: {' '.join(cmd)}")
            cls.logger.error(f"Return code: {exc.returncode}")
            raise
        except FileNotFoundError:
            raise RuntimeError(
                "mineru command not found. Please ensure MinerU is properly installed."
            )
        except Exception as exc:
            error_message = f"Unexpected error running mineru command: {exc}"
            cls.logger.error(error_message)
            raise RuntimeError(error_message) from exc

    MineruParser._run_mineru_command = _patched_run_mineru_command
    _PATCHED = True
    logger.info("✅ MinerU error detail patch applied (preserves full stderr details)")