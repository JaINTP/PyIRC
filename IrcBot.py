#! /user/bin/env python3

from datetime import datetime
from platform import system
from re import compile
from shlex import split
from socket import socket, AF_INET, SOCK_STREAM
from sys import exit
from time import sleep

__author__ = 'Jai Brown aka JaINTP'
__credits__ = ['Jai Brown', ]
__version__ = '1.0.0'
__maintainer__ = 'Jai Brown'
__email__ = 'j.brown.dev@gmail.com'


class _ConsoleColourer(object):
    """Basic class to handle the colouring of console output. Only
    supports ANSI escape sequences.
    """
    # TODO Add Windows support... LOL!

    __slots__ = [
        '__colours',
    ]

    def __init__(self):
        """Constructor.

        Initialises colour codes for formatting use.
        """
        super(_ConsoleColourer, self).__init__()
        self.__colours = {
            'w': 0,   # White
            'r': 31,  # Red
            'g': 32,  # Green
            'o': 33,  # Orange
            'b': 34,  # Blue
            'p': 35,  # Purple
            'c': 36,  # Cyan
            'G': 37,  # Grey
        }

    def _format(self, string: str) -> str:
        """Formats a given string.

        :type string:  String
        :param string: String to be formatted and printed.

        :rtype:        String
        :return:       The resulting formatted string.
        """
        base = '\033[{0}m'

        for char in self.__colours:
            if system() is 'Windows':
                string = string.replace('%' + char, '')
            else:
                string = string.replace('%' + char,
                                        base.format(self.__colours[char]))
                string = '{}\033[0m'.format(string)

        return string

    def print(self, string: str):
        """Outputs a given string in colour.

        :type string:  String
        :param string: String to be formatted and printed.
        """
        print(self._format(string))

    def input(self, string: str) -> str:
        """Outputs a given string in colour and waits for input.

        :type string:  String
        :param string: String to be formatted and printed.

        :rtype:        String
        :return:       The user's input string.
        """
        return input(self._format(string))
CC = _ConsoleColourer()


class Event(object):
    """ Basic event object. """

    __slots__ = [
        '__handlers',
    ]

    def __init__(self):
        """Constructor
        Initialises member variables.
        """
        self.__handlers = []

    def __iadd__(self, handler):
        """Adds a handler to the event.

        :type  handler: Method
        :param handler: Function to add to the event.
        :rtype:         Event
        :return:        The updated event object.
        """
        if handler not in self.__handlers:
            self.__handlers.append(handler)

        return self

    def __isub__(self, handler):
        """Removes a handler from the event.

        :type  handler: Method
        :param handler: Function to remove from the event.
        :rtype:         Event
        :return:        The updated event object.
        """
        if handler in self.__handlers:
            self.__handlers.remove(handler)

        return self

    def __call__(self, *args):
        """Calls all handlers linked to the event.

        :type  args: Array
        :param args: Event handler arguments.
        :rtype:      Event
        :return:     The updated event object.
        """
        for handler in self.__handlers:
            handler(*args)

        return self


class Server(object):
    """ Basic server object. """

    __slots__ = [
        '__ip',
        '__port',
    ]

    def __init__(self, ip: str, port=6667):
        """Constructor.
        Initialises member variables.

        :type  ip:   String
        :param ip:   Server IP address.
        :type  port: Int
        :param port: Server port.
        """
        self.__ip = ip
        self.__port = port

    @property
    def ip(self) -> str:
        """IP property getter.

        :rtype:  String
        :return: The server's IP address.
        """
        return self.__ip

    @ip.setter
    def ip(self, value: str):
        """IP property setter.

        :type  value: String
        :param value: New IP value.
        """
        self.__ip = value

    @property
    def port(self) -> str:
        """Port property getter.

        :rtype:  Int
        :return: The server's port.
        """
        return self.__port

    @port.setter
    def port(self, value: int):
        """Port property setter.

        :type  value: Int
        :param value: New Port value.
        """
        self.__port = value

    def as_tuple(self) -> str:
        """Returns the server's IP and Port in a tuple for socket
        initialisation.

        :rtype:  Tuple
        :return: Tuple containing the server's IP and Port.
        """
        return self.__ip, self.__port


class Config(object):
    """ Basic class encapsulating irc bot configurations. """

    __slots__ = [
        '__command_char',
        '__channel',
        '__file',
        '__nick',
        '__password',
        '__server',
    ]

    def __init__(self, filename: str):
        """Constructor.
        Initialises member variables.

        :type  filename: String
        :param filename: The name of the configuration file in the current
                         working directory.
        """
        self.__command_char = None
        self.__channel = None
        self.__file = filename
        self.__nick = None
        self.__password = None
        self.__server = None
        self.__get_config()

    def __get_config(self):
        """Reads the contents of the configuration file and binds them to their
        respective variables.
        """
        with open(self.__file, 'r') as f:
            content = [line.rstrip() for line in f.readlines()]

        for setting in content:
            setting = [item.lstrip().rstrip() for item in setting.split(':')]

            attribute = '_Config__{0}'.format(setting[0])
            if hasattr(self, attribute):
                setattr(self, attribute, setting[1])

    def get(self, setting: str):
        """Gets a given attribute from the configuration.

        :type    setting: String
        :param   setting: The name of the setting to retrieve.
        :rtype:           String, Int
        :return:          The value of the configuration parameter.
        """
        setting = '_Config__{0}'.format(setting)
        if hasattr(self, setting):
            return getattr(self, setting)

    def write_basic_config(self):
        """ Writes a basic example configuration file. """
        with open(self.__file, 'w') as f:
            f.writelines(['nick: jaintp_bot',
                          'server: irc.freenode.net',
                          'password: lolYouWish!',
                          'channel: #jaintp',
                          'command_char: !'])


class Bot(object):
    """ Basic IRC bot example. """

    __slots__ = [
        # Member Variables.
        '__config',
        '__connected',
        '__debug',
        '__nick',
        '__owners',
        '__pat',
        '__plugins',
        '__server',
        '__soc',
        # Events.
        '__irc_COMMAND',
        '__irc_JOIN',
        '__irc_KICK',
        '__irc_MODE',
        '__irc_NOTICE',
        '__irc_PRIVMSG',
    ]

    def __init__(self, config_file='irc.cfg', debug=False):
        """Constructor.

        Initialises member variables.

        :type  config_file: String
        :param config_file: Configuration file name.
        :type  debug:       Boolean
        :param debug:       Whether or not to print debug output.
        """
        self.__config = Config(config_file)
        self.__connected = False
        self.__debug = debug
        self.__nick = self.__config.get('nick')
        self.__owners = ('JaINTP',)  # Hardcoded for now.
        self.__pat = compile(':([^!]+)!(\S+)\s+(\S+)\s+:?(\S+)'
                             '\s*(?:[:+-]+(.*))?(?:[:+-]+(.*))?')
        self.__plugins = []  # To be implemented later...
        self.__server = Server(self.__config.get('server'))
        self.__soc = socket(AF_INET, SOCK_STREAM)
        # Events.
        self.__irc_COMMAND = Event()
        self.__irc_JOIN = Event()
        self.__irc_KICK = Event()
        self.__irc_MODE = Event()
        self.__irc_NOTICE = Event()
        self.__irc_PRIVMSG = Event()

    def init_events(self):
        """ Initialises all built-in event handlers. """
        self.__irc_COMMAND += self.on_command
        self.__irc_KICK += self.on_kick
        self.__irc_MODE += self.on_mode
        self.__irc_COMMAND += self.on_privmsg

    def connect(self):
        """ Connects to the IRC server, identifies and moves on. """
        self.__soc.connect(self.__server.as_tuple())
        self.send_action('NICK', self.__nick)
        self.send_action('USER',
                         '{0} PyBot PyBot :JaINTP\'s Python IRC bot.'
                         .format(self.__nick))
        self.debug_out('%oIdentifying%g...')
        self.send_msg('Nickserv',
                      'identify {0}'.format(self.__config.get('password')))
        sleep(5)
        self.__connected = True

    def mainloop(self):
        """ Main IRC client logic. """
        self.init_events()
        self.connect()

        while self.__connected:
            data = self.__soc.recv(1024).decode('utf-8')

            if data.startswith('PING'):
                self.send_action('PONG', data.split()[-1])
                self.debug_out('%oPONG%g: %o{0}'.format(data.split()[-1]))
            else:
                self.handle_msg(data)
                self.debug_out("%o{}".format(data))

            # To be removed later...
            if 'End of /MOTD' in data:
                self.debug_out('%oMOTD done%g!')
                self.join(self.__config.get('channel'))

    def handle_msg(self, data: str):
        """Handles data received from the IRC server.

        :type  data: String
        :param data: Message received from the IRC server.
        """
        reg = self.__pat.match(data)

        if reg is not None:
            g = reg.groups()

            com = dict(zip(['nick', 'user', 'action', 'recipient', 'message'],
                           [item.rstrip() for item in g if item is not None]))
            com['orig'] = data

            try:
                self.debug_out('%oCalling event handler for {0}'.format(
                    com['action']))
                getattr(self, 'irc_{0}'.format(com['action']))(com)
            except AttributeError:
                pass  # No event handler for the event\command.

    def send(self, string: str):
        """Handles sending a string to the IRC server.

        :type  string: String
        :param string: The string to be sent.
        """
        try:
            self.__soc.send('{0}\r\n'.format(string).encode())
        except Exception as e:
            self.debug_out(str(e))

    def send_action(self, action: str, argument_string: str):
        """Sends a given action message to the IRC server.

        :type  action:          String
        :param action:          The action to be sent.
        :type  argument_string: String
        :param argument_string: The string to be sent.
        """
        self.send('{0} {1}'.format(action, argument_string))

    def join(self, chan: str):
        """Performs a JOIN action.

        :type  chan: String
        :param chan: The channel to join.
        """
        self.send_action('JOIN', chan)

    def quit(self):
        """ Performs a QUIT action. """
        self.send('QUIT')
        self.__soc.close()
        exit(0)

    def send_msg(self, recip: str, message: str):
        """Performs a PRIVMSG action.

        :type  recip:   String
        :param recip:   The recipient of the message.
        :type  message: String
        :param message: The message to be sent to the recipient.
        """
        self.send_action('PRIVMSG', '{0} :{1}'.format(recip, message))

    def debug_out(self, string: str):
        """Prints debug messages to stdout.

        :type  string: String
        :param string: String to be printed.
        """
        if self.__debug:
            output = []

            if '\n' in string:
                output = string.split('\n')
            else:
                output = [string, ]

            for item in output:
                if item is not '':
                    CC.print("%o{0}%g[%bDebug%g] - {1}"
                             .format(datetime.now()
                                             .strftime('%H:%M:%S')
                                             .replace(':', '%g:%o'),
                                     item))

    # Event Handlers:
    def on_command(self, data: dict):
        """IRC bot command handler.

        Handles built in commands and passes others to their prospective
        plugins.

        :type  data: Dict
        :param data: Dictionary containing command data.
        """
        self.debug_out('%oHandling command%g: %o{0}'
                       .format(data['message'][0]))

        if data['nick'] in self.__owners:
            if data['message'][0] == 'die':
                self.debug_out("%oQuitting%g...")
                self.quit()
                return  # Bad hack for now...

        # To be implemented later...
        # for plugin in self.__plugins:
        #     if plugin.command == data['message'][0]:
        #         plugin.func(data['message'][1:])

    def on_privmsg(self, data: dict):
        """Basic event handler for PRIVMSG actions.

        :type  data: Dict
        :param data: Dictionary containing an IRC message.
        """
        if data['message'][0] == self.__config.get('cchar'):
            data['message'] = split(data['message'][1:])
            self.debug_out('%oReceived command%g, %o{0}%g, %ofrom {1}'
                           .format(data['message'][0], data['nick']))
            self.__irc_COMMAND(data)

    def on_kick(self, data: dict):
        """Basic event handler for KICK actions.

        :type  data: Dict
        :param data: Dictionary containing an IRC KICK message data.
        """
        tmp = data['orig'].split()

        if tmp[3] == self.__nick:
            self.join(tmp[2])

    def on_mode(self, data: dict):
        """Basic event handler for KICK actions.

        :type  data: Dict
        :param data: Dictionary containing an IRC MODE message data.
        """
        # TODO Implement this method.
        pass


if __name__ == '__main__':
    bot = Bot(debug=True)
    bot.mainloop()

# vim: set ts=4 sw=4 tw=80 ff=unix :
