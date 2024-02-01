from typing import TYPE_CHECKING
import socket
import logging

logger = logging.getLogger("mains.mqtt")


if TYPE_CHECKING:
    from typing import List, Tuple
    from desim.core import Simulation
    from desim.core import Simulation
    from sim.item import Product

import paho.mqtt.publish
import paho.mqtt.client

mqtt_server_available = None  # type: ignore


def send_data_to_mqtt(core: Simulation[Product]):
    logger.debug("Sending data to MQTT server")
    # MQTT server checking
    if mqtt_server_available is None:  # type: ignore
        logger.info("Checking if MQTT server is available")

        # Check if port 80 is open

        sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        result = sock.connect_ex(("127.0.0.1", 80))
        if result == 0:
            logger.info("MQTT server expected port is open")
            mqtt_server_available = 1  # type: ignore
        else:
            logger.info("MQTT server expected port is not open")
            mqtt_server_available = -1  # type: ignore
            return
        sock.close()

    elif mqtt_server_available == -1:  # type: ignore
        return

    msg_list: List[Tuple[str, str | None, int, bool]] = [
        ("desym/step", str(core.timed_events_manager.step), 0, False)
    ]

    for stopper in core.stoppers.values():
        if stopper.container is not None:
            msg_list.append(
                (
                    f"desym/stopper/{stopper.id}/container",
                    str(f"Id: {stopper.container.id} {stopper.container.content}"),
                    0,
                    False,
                )
            )
        else:
            msg_list.append((f"desym/stopper/{stopper.id}/container", None, 0, False))

    for conveyor in core.conveyors.values():
        if conveyor.container is not None:
            msg_list.append(
                (
                    f"desym/conveyor/{conveyor.id}/container",
                    str(f"Id: {conveyor.container.id} {conveyor.container.content}"),
                    0,
                    False,
                )
            )
        else:
            msg_list.append((f"desym/conveyor/{conveyor.id}/container", None, 0, False))

    paho.mqtt.publish.multiple(
        msg_list,  # type: ignore
        hostname="localhost",
        port=1883,
        client_id="",
        keepalive=60,
        will=None,
        auth=None,
        tls=None,
        protocol=paho.mqtt.client.MQTTv311,
        transport="tcp",
    )
