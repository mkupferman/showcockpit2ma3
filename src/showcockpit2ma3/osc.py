#!/usr/bin/env python3

from typing import List, Tuple, Any, Self, Optional, Type, cast
from types import TracebackType
from collections.abc import Callable, Mapping

import threading
import queue

from pythonosc.dispatcher import Dispatcher
from pythonosc.osc_server import BlockingOSCUDPServer
from pythonosc import udp_client


class OSCProxy:
    def __init__(
        self,
        sc_listen_ip: str,
        ma_listen_ip: str,
        ma_ip: str,
        ma_input_port: int,
        ma_output_port: int,
        sc_ip: str,
        sc_input_port: int,
        sc_output_port: int,
        sc_datapool_base: str,
        ma_datapool_base: str,
        verbose: bool = False,
    ) -> None:
        self.sc_listen_ip = sc_listen_ip
        self.ma_listen_ip = ma_listen_ip
        self.ma_ip = ma_ip
        self.ma_input_port = ma_input_port
        self.ma_output_port = ma_output_port
        self.sc_ip = sc_ip
        self.sc_input_port = sc_input_port
        self.sc_output_port = sc_output_port
        self.sc_datapool_base = sc_datapool_base
        self.ma_datapool_base = ma_datapool_base
        self.verbose = verbose

        self.scInputQueue: queue.Queue[tuple[str, tuple[Any, ...]]] = queue.Queue()
        self.scOutputQueue: queue.Queue[tuple[str, tuple[Any, ...]]] = queue.Queue()
        self.maInputQueue: queue.Queue[tuple[str, tuple[Any, ...]]] = queue.Queue()
        self.maOutputQueue: queue.Queue[tuple[str, tuple[Any, ...]]] = queue.Queue()

        self.threads: queue.Queue[threading.Thread] = queue.Queue()
        self.killSwitch: bool = False

    def _sc2ma(self, address: str, *args: Tuple[Any]) -> None:
        """
        Performs replacement on the address string to convert from ShowCockpit to MA3 format.
        Reconstructs the OSC message and places it in the MA3 output queue.
        """

        if self.verbose:
            print(f"[SC ->] {address} {args}")

        address = address.replace(self.sc_datapool_base, self.ma_datapool_base)

        largs = list(cast(List[Any], args))
        if largs[0] == "Swop":
            largs[0] = "Swap"

        self.maOutputQueue.put((address, tuple(largs)))

        if self.verbose:
            print(f"[-> MA] {address} {largs}", flush=True)

    def _ma2sc(self, address: str, *args: Tuple[Any]) -> None:

        if self.verbose:
            print(f"[MA ->] {address} {args}")

        address = address.replace(self.ma_datapool_base, self.sc_datapool_base)

        largs = list(cast(List[Any], args))
        if largs[0] == "Swap":
            largs[0] = "Swop"

        self.scOutputQueue.put((address, tuple(largs)))

        if self.verbose:
            print(f"[-> SC] {address} {largs}", flush=True)

    def _oscServer(
        self,
        source: str = "sc",
        listen: str = "127.0.0.1",
        port: int = 8000,
        queue: Optional[queue.Queue[tuple[str, tuple[Any, ...]]]] = None,
    ) -> None:
        print(f"Starting OSC Server for {source} on {listen}:{port}")
        dispatcher = Dispatcher()
        if source == "sc":
            dispatcher.set_default_handler(self._sc2ma)
        else:
            dispatcher.set_default_handler(self._ma2sc)

        server = BlockingOSCUDPServer((listen, port), dispatcher)

        if source == "sc":
            self.scServer = server
        elif source == "ma":
            self.maServer = server

        server.serve_forever()

        print(f"OSC Server for {source} shutting down")

    def _startThread(
        self,
        target: Callable[[], None],
        kwargs: Optional[Mapping[str, Any]] = None,
        daemon: bool = True,
    ) -> None:
        """Start a thread with the specified target and kwargs.
        Track the running threads in a queue so we can join them
        when exiting to ensure they complete properly.
        """

        thread = threading.Thread(target=target, kwargs=kwargs, daemon=daemon)
        thread.start()
        self.threads.put(thread)

    def _outputQueue(
        self,
        dest: str = "sc",
        queue: queue.Queue[tuple[str, tuple[Any, ...]]] = queue.Queue(),
    ) -> None:
        # set up output client
        if dest == "sc":
            client = udp_client.SimpleUDPClient(self.sc_ip, self.sc_input_port)
        else:
            client = udp_client.SimpleUDPClient(self.ma_ip, self.ma_input_port)

        while not self.killSwitch or self.killSwitch and not queue.empty():
            if not queue.empty():
                address, args = queue.get()
                client.send_message(address, args)

    def serve(self) -> None:
        self._startThread(
            self._oscServer,
            kwargs={
                "source": "sc",
                "listen": self.sc_listen_ip,
                "port": self.sc_output_port,
                "queue": self.scInputQueue,
            },
        )
        self._startThread(
            self._oscServer,
            kwargs={
                "source": "ma",
                "listen": self.ma_listen_ip,
                "port": self.ma_output_port,
                "queue": self.maInputQueue,
            },
        )
        self._startThread(
            self._outputQueue, kwargs={"dest": "sc", "queue": self.scOutputQueue}
        )
        self._startThread(
            self._outputQueue, kwargs={"dest": "ma", "queue": self.maOutputQueue}
        )

    def _drainThreads(self) -> None:
        while not self.threads.empty():
            thread = self.threads.get()
            if thread and thread.is_alive():
                try:
                    thread.join()
                except:
                    pass

    def __enter__(self) -> Self:
        return self

    def __exit__(
        self,
        type: Optional[Type[BaseException]],
        value: Optional[BaseException],
        traceback: Optional[TracebackType],
    ) -> None:
        self.stop()

    def __del__(self) -> None:
        self.stop()

    def stop(self) -> None:
        self.killSwitch = True
        try:
            self.scServer.shutdown()
            self.maServer.shutdown()
        except:
            pass
        self._drainThreads()
