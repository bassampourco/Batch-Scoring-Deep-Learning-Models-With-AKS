from azure.servicebus import ServiceBusService, Message, Queue
from azure.storage.blob import BlockBlobService
from util import Parser, get_handler_format
import time
import sys
import subprocess
import os
import logging
from util import Parser


def add_images_to_queue(
    input_dir_name, output_dir_name, queue, bus_service, queue_limit=None
):
    """
    :param input_dir: the input directory where the frames are stored
    :param output_dir: the output directory where we want to store the processed frames
    :param storage_container: the storage container of the above three params
    :param queue: the queue to add messages to
    :param queue_limit: (optional) an optional queue limit to stop queuing at
    :param block_blob_service: blob client
    :param bus_service: service bus client
    """
    t0 = time.time()

    # set input/output dirs
    input_dir = os.path.join("data", input_dir_name)
    output_dir = os.path.join("data", output_dir_name)

    # count number of frames in input dir
    path, dirs, files = next(os.walk(input_dir))
    file_count = len(files)

    # set up variables for adding messages to the queue in batch
    msg_batch = []
    batch_size = 500

    # iterate through all images in input dir
    for i, filename in enumerate(os.listdir(input_dir)):

        if queue_limit is not None and i >= queue_limit:
            logger.debug("Queue limit is reached. Exiting process...")
            exit(0)

        msg_body = {
            "input_frame": filename,
            "input_dir": input_dir_name,
            "output_dir": output_dir_name,
        }
        msg = Message(str(msg_body).encode())
        msg_batch.append(msg)

        if i > 0:
            if queue_limit:
                condition = i % batch_size == 0 or i == queue_limit - 1
            else:
                condition = i % batch_size == 0 or i == file_count - 1

            if condition:
                bus_service.send_queue_message_batch(queue, msg_batch)
                msg_batch = []

    t1 = time.time()
    logger.debug("Adding image to queue finished. Time taken: {:.2f}".format(t1 - t0))


if __name__ == "__main__":

    parser = Parser()
    parser.append_add_images_to_queue_args()
    args = parser.return_args()

    assert args.input_dir is not None
    assert args.output_dir is not None
    assert args.namespace is not None
    assert args.queue is not None
    assert args.sb_key_name is not None
    assert args.sb_key_value is not None

    # setup logger
    handler_format = get_handler_format()
    console_handler = logging.StreamHandler(sys.stdout)
    console_handler.setFormatter(handler_format)
    logger = logging.getLogger("root")
    logger.setLevel(logging.DEBUG)
    logger.addHandler(console_handler)
    logger.propagate = False

    bus_service = ServiceBusService(
        service_namespace=args.namespace,
        shared_access_key_name=args.sb_key_name,
        shared_access_key_value=args.sb_key_value,
    )

    add_images_to_queue(
        input_dir_name=args.input_dir,
        output_dir_name=args.output_dir,
        queue=args.queue,
        bus_service=bus_service,
        queue_limit=args.queue_limit,
    )
