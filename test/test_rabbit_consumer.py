import multiprocessing

import pika
import time


def consumer_logic(channel):
    channel.queue_declare(queue="hello")
    for message in channel.consume(queue="hello", auto_ack=True):
        print("received")


if __name__ == "__main__":
    connection = pika.BlockingConnection(pika.ConnectionParameters(host="10.134.149.124"))
    channel_tmp = connection.channel()
    process = multiprocessing.Process(target=consumer_logic, args=(channel_tmp, ))
    process.start()
    input("(press any key to stop)")
    while True:
        test = input("q to quit")
        if test == "q":
            break
