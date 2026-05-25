from __future__ import annotations

import argparse
import asyncio
import json
import signal
import sys

from parrot_studio.ipc.control_server import ControlServer
from parrot_studio.job_controller import JobController


async def run_backend() -> None:
    control = ControlServer()
    controller = JobController(control.send_event)
    control.set_command_handler(controller.handle_command)
    await control.start()

    print(json.dumps({"type": "ready", "control_port": control.port}), flush=True)

    stop = asyncio.Event()
    loop = asyncio.get_running_loop()
    for sig in (signal.SIGTERM, signal.SIGINT):
        try:
            loop.add_signal_handler(sig, stop.set)
        except NotImplementedError:
            pass
    await stop.wait()
    await controller.stop()
    await control.stop()


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--check", action="store_true")
    parser.add_argument("--dev", action="store_true")
    args = parser.parse_args()
    if args.check:
        print("parrot studio backend ok")
        return 0
    try:
        asyncio.run(run_backend())
    except KeyboardInterrupt:
        return 0
    except Exception as exc:
        print(json.dumps({"type": "fatal", "message": str(exc)}), file=sys.stderr, flush=True)
        return 1
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
