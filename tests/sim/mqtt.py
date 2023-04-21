from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from desym.core import Simulation

import paho.mqtt.publish
import paho.mqtt.client


def send_data_to_mqtt(core: Simulation):
    msg_list = [("desym/step", str(core.events_manager.step), 0, False)]

    for stopper in core.stoppers.values():
        if stopper.input_tray is not None:
            if stopper.input_tray.item:
                item_string = f" T: {stopper.input_tray.item.item_type.value} S: {stopper.input_tray.item.state}"
            else:
                item_string = ""
            msg_list.append(
                (
                    f"desym/stopper/{stopper.stopper_id}/input",
                    str(f"Id: {stopper.input_tray.tray_id} {item_string}"),
                    0,
                    False,
                )
            )
        else:
            msg_list.append(
                (f"desym/stopper/{stopper.stopper_id}/input", None, 0, False)
            )

        for output_tray_id in stopper.output_trays:
            if stopper.output_trays[output_tray_id]:
                if stopper.output_trays[output_tray_id].item:
                    item_string = f"T: {stopper.output_trays[output_tray_id].item.item_type.value} S: {stopper.output_trays[output_tray_id].item.state}"
                else:
                    item_string = ""
                msg_list.append(
                    (
                        f"desym/stopper/{stopper.stopper_id}/output/{output_tray_id}",
                        str(
                            f"Id: {stopper.output_trays[output_tray_id].tray_id} {item_string}"
                        ),
                        0,
                        False,
                    )
                )
            else:
                msg_list.append(
                    (
                        f"desym/stopper/{stopper.stopper_id}/output/{output_tray_id}",
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