#!/usr/bin/env python3

from typing import Any
import click

from showcockpit2ma3.osc import OSCProxy


@click.command()
@click.option(
    "--sc-listen-ip",
    default="127.0.0.1",
    help="The ip to listen on for ShowCockpit OSC",
)
@click.option(
    "--ma-listen-ip", default="127.0.0.1", help="The ip to listen on for MA3 OSC"
)
@click.option("--ma-ip", default="127.0.0.1", help="The ip of the MA3 console")
@click.option(
    "--ma-input-port",
    type=click.INT,
    default=8000,
    help="The port the MA3 console is listening on",
)
@click.option(
    "--ma-output-port",
    type=click.INT,
    default=8001,
    help="The port the MA3 console is sending on",
)
@click.option("--sc-ip", default="127.0.0.1", help="The ip of ShowCockpit")
@click.option(
    "--sc-input-port",
    type=click.INT,
    default=8101,
    help="The port the ShowCockpit is listening on",
)
@click.option(
    "--sc-output-port",
    type=click.INT,
    default=8100,
    help="The port the ShowCockpit is sending on",
)
@click.option(
    "--sc-datapool-base",
    default="/13.13.",
    help="The base path for ShowData.DataPools known in ShowCockpit",
)
@click.option(
    "--ma-datapool-base",
    default="/14.14.",
    help="The base path for ShowData.DataPools known in MA3",
)

# verbose flag
@click.option(
    "--verbose", "-v", is_flag=True, help="Print verbose output", default=False
)
def startServer(**params: Any) -> None:
    osc = OSCProxy(**params)
    osc.serve()

    while True:
        cmd = input("Enter 'q' to quit: ")
        if cmd == "q":
            osc.stop()
            break
