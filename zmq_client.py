#!/usr/bin/env python3

# PervasID client v0.1
# Copyright Anton Samofal 2020 [GETS]

import zmq
import argparse
import json
import datetime
from colorama import Fore as Color, Style, init as colorama_init

# Config
SERVER_IP = '10.57.50.10'
SERVER_PORT = '10904'

# init arguments parser
parser = argparse.ArgumentParser(description='PervasID control center')
parser.add_argument('-hw_addr', help='filter by hardware address of the reader')
args = parser.parse_args()


def main():
    # display "welcome" text
    print_greeting()

    menu_items = {
        1: 'Subscribe to connections status queue',
        2: 'Subscribe to tags reading queue',
        3: 'Publish a command to commands queue'
    }
    main_menu = Menu(menu_items)
    main_menu_choice = main_menu.ask_to_choose()
    handle_main_menu_choice(main_menu_choice)


def print_greeting():
    greeting = f'{Color.GREEN}{Style.BRIGHT}Welcome to PervasID client{Style.RESET_ALL}{Color.RESET}'
    print(f"{Color.BLUE}{12 * '*'} {greeting} {Color.BLUE}{12 * '*'}")


def handle_main_menu_choice(choice: int):
    if choice == 1:
        filter_question = f'{Style.BRIGHT}Filter by HwAddr (keep empty to skip filtering):{Style.RESET_ALL} '
        hw_addr = input(filter_question)
        while len(hw_addr) > 0 and hw_addr.isdigit() is False:
            print(f'{Color.RED}Wrong HwAddr format! Only numeric type is allowed.')
            hw_addr = input(filter_question)

        if len(hw_addr) > 0:
            filter_state_msg = f'Subscribe with filter by hwAddr: {Color.WHITE}{Style.BRIGHT}{hw_addr}.'
        else:
            filter_state_msg = 'Subscribe without filter.'
        print('')
        print(f'{Color.GREEN}{filter_state_msg}')

        SubscriberConnectionsStatus(hw_addr)
    elif choice == 2:
        print(choice)
    elif choice == 3:
        print(choice)
    else:
        raise ValueError


class Menu:
    items: dict

    def __init__(self, items):
        self.items = items

        self.print_available_commands()

    def print_available_commands(self):
        print('')

        menu_items_template = []
        for key in self.items:
            menu_items_template.append(f'{Color.RED}{key}. {Color.YELLOW}{self.items[key]}')

        menu_items_template = "\n".join(menu_items_template)
        print(menu_items_template)

    def ask_to_choose(self) -> int:
        print('')

        item_indices = []
        for key in self.items.keys():
            item_indices.append(str(key))

        item_indices_str = '/'.join(item_indices)
        question = f'{Style.BRIGHT}Please enter your choice {Style.RESET_ALL}[{item_indices_str}]: '

        choice = input(question)
        while choice not in item_indices:
            print(f'{Color.RED}Unsupported value, be attentive ;)')
            choice = input(question)

        return int(choice)


class SubscriberConnectionsStatus:
    hw_addr: int or None = None
    device_id: int or None = None

    def __init__(self, hw_addr: str):
        if len(hw_addr) > 0:
            self.hw_addr = int(hw_addr)
            self.device_id = convert_hw_addr_to_device_id(self.hw_addr)

        # ZeroMQ socket to talk to server
        socket = self.init_socket_connection()

        try:
            while True:
                response = socket.recv_multipart()
                message_items = []

                # decode response body
                data = json.loads(response[1].decode())

                # format and print a message
                print(Message.reader_status(data))
        except KeyError:
            pass

    def init_socket_connection(self) -> zmq.sugar.socket.Socket:
        context = zmq.Context()
        socket = context.socket(zmq.SUB)

        socket.connect(f'tcp://{SERVER_IP}:{SERVER_PORT}')

        subscribe_filter = f'reader_status/{self.device_id}' if self.device_id is not None else ''
        socket.setsockopt_string(zmq.SUBSCRIBE, subscribe_filter)

        print('')
        start_msg = f'{Color.BLUE}{Style.BRIGHT}Socket connection established:{Style.RESET_ALL} '
        start_msg += f'{Color.CYAN}{SERVER_IP}:{SERVER_PORT}{Color.BLUE}'
        print(start_msg)

        return socket


class Message:
    @staticmethod
    def reader_status(data: dict) -> str:
        message_items = []

        hw_addr_formatted = "{:<15}".format(data['HWAddr'])
        message_items.append(f"{Color.RED}HWAddr: {Color.GREEN}{hw_addr_formatted}{Color.RESET}")

        message_items.append(f"{Color.RED}status: {Color.GREEN}{data['status']}{Color.RESET}")

        ip = "{:<12}".format(data['inet_address'])
        message_items.append(f"{Color.RED}ip: {Color.GREEN}{ip}{Color.RESET}")

        reader_version = "{:<7}".format(data['reader_version'])
        message_items.append(f"{Color.RED}reader_version: {Color.GREEN}{reader_version}{Color.RESET}")

        radio_version = "{:<12}".format(data['radio_version'])
        message_items.append(f"{Color.RED}radio_version: {Color.GREEN}{radio_version}{Color.RESET}")

        message_items.append(f"{Color.RED}tag_reads: {Color.GREEN}{data['tag_reads']}{Color.RESET}")

        timestamp_in_seconds = data['timestamp'] / 1000
        time = f"[{datetime.datetime.fromtimestamp(timestamp_in_seconds):%H:%M:%S}] "

        return time + ' | '.join(message_items)


def convert_hw_addr_to_device_id(hw_addr: int) -> str:
    hw_addr_hex = format(hw_addr, 'x')
    device_id = "".join(reversed([hw_addr_hex[i:i + 2] for i in range(0, len(hw_addr_hex), 2)]))

    return device_id


if __name__ == '__main__':
    # init colorama module
    colorama_init(autoreset=True)

    try:
        main()
    except KeyboardInterrupt:
        print('')
        exit(0)