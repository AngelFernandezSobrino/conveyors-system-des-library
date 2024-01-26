from typing import TYPE_CHECKING, List, Tuple

from tests.sim.logger import logger

from desym.core import Simulation

if TYPE_CHECKING:
    from desym.core import Simulation

import paho.mqtt.publish
import paho.mqtt.client


def send_data_to_mqtt(core: Simulation):
    # Check if static variable is defined
    if send_data_to_mqtt.mqtt_server_available is None:  # type: ignore
        # Check if port 80 is open
        import socket

        sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        result = sock.connect_ex(("127.0.0.1", 80))
        if result == 0:
            logger.info("Port is open")
            send_data_to_mqtt.mqtt_server_available = 1  # type: ignore
        else:
            logger.info("Port is not open")
            send_data_to_mqtt.mqtt_server_available = -1  # type: ignore
            return
        sock.close()

    elif send_data_to_mqtt.mqtt_server_available == -1:  # type: ignore
        return

    msg_list: List[Tuple[str, str, int, bool]] = [
        ("desym/step", str(core.timed_events_manager.step), 0, False)
    ]

    for stopper in core.stoppers.values():
        if stopper.input_container is not None:
            if stopper.input_container.content:
                item_string = f" T: {stopper.input_container.content.item_type.value} S: {stopper.input_container.content.state}"
            else:
                item_string = ""
            msg_list.append(
                (
                    f"desym/stopper/{stopper.id}/input",
                    str(f"Id: {stopper.input_container.id} {item_string}"),
                    0,
                    False,
                )
            )
        else:
            msg_list.append((f"desym/stopper/{stopper.id}/input", None, 0, False))

        for output_tray_id in stopper.output_trays:
            if stopper.output_trays[output_tray_id]:
                if stopper.output_trays[output_tray_id].content:
                    item_string = f"T: {stopper.output_trays[output_tray_id].content.item_type.value} S: {stopper.output_trays[output_tray_id].content.state}"
                else:
                    item_string = ""
                msg_list.append(
                    (
                        f"desym/stopper/{stopper.id}/output/{output_tray_id}",
                        str(
                            f"Id: {stopper.output_trays[output_tray_id].id} {item_string}"
                        ),
                        0,
                        False,
                    )
                )
            else:
                msg_list.append(
                    (
                        f"desym/stopper/{stopper.id}/output/{output_tray_id}",
                        None,
                        0,
                        False,
                    )
                )

    paho.mqtt.publish.multiple(
        msg_list,
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


send_data_to_mqtt.mqtt_server_available = None  # type: ignore
