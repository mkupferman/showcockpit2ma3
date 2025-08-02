# ShowCockpit to GrandMA3

This is effectively a bidirectional OSC proxy to sit between ShowCockpit and GrandMA3.

Its main purpose is to act as a temporary "bandage", correcting for procotol differences between ShowCockpit v4.11.2 and GrandMA3 v2.2.1

Once one or both of the two vendors makes updates, this tool hopefully will not be needed anymore.

## What does it alter?

At the time of writing, I know of several protocol inconsistencies between ShowCockpit 4.11.2 and GrandMA3 2.2.1+:

1. Between GrandMA3 2.1.1 and 2.2.1, the numerical indexing of the MA3 directory structure changed.
   `ShowData` and `DataPools` both changed from ID `13` to `14`, making sequence-based OSC messages
   change from address `/13.13.1.6.X` to `/14.14.1.6.X`.

2. For _swop_ functionality on a sequence button, the GrandMA3 OSC protocol expects `Swap` instead of `Swop`.

3. Between GrandMA3 2.0.2.0 and 2.1.1.2, it stopped sending a 4th OSC argument for Fader feedback messages,
   and ShowCockpit expects 4 arguments. This proxy will add a dummy 4th argument to these messages.

4. When GrandMA3 sends sequence off messages with format `/14.14.1.6.X 'Off' 1`, ShowCockpit expects
   a different format: `/13.13.1.6.X 'Go+' 0 '<any arg>'`. This proxy translates the first argument from
   `Off` to `Go+`, changes the second argument from `1` to `0`, and adds a dummy third argument.

## Requirements

* Computer running [ShowCockpit](https://showcockpit.com/) 4.11.2.
* Console or onPC running [GrandMA3](https://www.malighting.com/grandma3/) at least 2.2.1
  (also confirmed on 2.2.5 and 2.3.0).
* Computer to run the proxy on, with Python 3.11 or later. In most cases, this
  can be on the same computer as ShowCockpit.
* UDP network connectivity between all devices.

## Quick start

1. Install the proxy on a computer with Python 3.11 or later. Python virtual
   environments are recommended.

    ```shell
    python3 -m pip install .
    ```

2. Modify your current ShowCockpit GrandMA3 driver IP/port settings to point
   to the proxy's IP and ports.
   For example, GrandMA3 listens for incoming OSC on port 8000 and sends outgoing OSC on port 8001,
   and the proxy is running on the same computer as ShowCockpit, you might set ShowCockpit to send OSC to
   127.0.0.1 (don't forget to choose the correct network interface in the dropdown) with outbound port 8100
   and inbound port 8101.

3. Run the proxy with the correct ports and IP addresses. For example, if GrandMA3 is at 192.168.1.100 and
   and the proxy is running on the same computer as ShowCockpit which also has IP 192.168.1.200:

    ```shell
    showcockpit2ma3 \
      --ma-listen-ip 192.168.1.200 \  # proxy listens for MA's OSC on this local IP
      --ma-output-port 8001 \         # ... and binds to this local port
      --ma-ip 192.168.1.100 \         # proxy sends OSC to MA on this IP
      --ma-input-port 8000 \          # ... and this port
      --sc-listen-ip 127.0.0.1 \      # proxy listens for SC's OSC on this local IP
      --sc-output-port 8100 \         # ... and binds to this local port
      --sc-ip 127.0.0.1 \             # proxy sends OSC to SC on this IP
      --sc-input-port 8101 \          # ... and this port
    ```

## Usage Notes

If running the proxy on the same computer as GrandMA3 onPC, you might need to start the proxy before enabling
the OSC lines in MA3 becuase of the way MA3 binds to the UDP ports. If you get an error about the port being in use,
try starting the proxy first.
