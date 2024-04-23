import pika


def provider_logic(connection_tmp: pika.BlockingConnection):
    channel = connection_tmp.channel()
    channel.queue_declare(queue="hello")
    message = input("please input message:")
    channel.basic_publish(exchange="",
                          routing_key="hello",
                          body=message.encode("utf-8"))
    print(" [x] Sent %r" % message)


if __name__ == "__main__":
    connection = pika.BlockingConnection(pika.ConnectionParameters(host="10.134.149.124"))
    provider_logic(connection)
