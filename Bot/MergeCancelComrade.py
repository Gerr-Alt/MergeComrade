import json
import logging
import os
import sys
from logging.handlers import RotatingFileHandler

import flask
import pickle
import telebot
from pickle import PickleError

from telebot.apihelper import ApiException

try:
    import Bot
except ImportError:
    BOT_PATH = os.path.realpath(os.path.dirname(os.path.dirname(__file__)))
    sys.path.append(BOT_PATH)
    import Bot

from Bot.MergeDispatcher import BotModel
from Bot.MergeDispatcher import BotPresentationModel
from Bot.MergeDispatcher import Dispatcher
from Bot.MergeDispatcher import JSONConfigLoader
from Bot.MergeDispatcher import MessageSender
from Bot.MergeDispatcher import States

BOT_VERSION_STRING = "0.9"

BACKUP_FOLDER_NAME = "backup"
LOGS_FOLDER_NAME = "logs"

BOT_LOG_FILENAME = "mergebot.log"
CHANGELOG_FILENAME = "CHANGELOG"
CONFIG_FILENAME = "config.json"
SILENT_RESTART_FILENAME = "SILENT"

CALLBACK_COMMAND_NAME = "com"
CALLBACK_COMMAND_BRANCH_SELECTOR = "sel"
CALLBACK_COMMAND_USER_SELECTOR = "usr"
CALLBACK_COMMAND_CANCEL = "cnl"
CALLBACK_COMMAND_MERGE_CONFIRM = "mrg_cfm"
CALLBACK_COMMAND_MERGE_CANCEL = "mrg_cnl"
CALLBACK_BRANCH_NAME = "branch"
CALLBACK_USER_ID = "usr_id"

ENV_VARIABLE_TOKEN = "TOKEN"
ENV_VARIABLE_WORKING_DIR = "WORKING_DIR"

ENV_VARIABLE_WEBHOOK_ENABLED = "WEBHOOK"
ENV_VARIABLE_PORT = "PORT"
ENV_VARIABLE_HOST = "VIRTUAL_HOST"


class UIState:
    def __init__(self, current_state=None, current_branch_filter=None):
        self._current_state = current_state
        self._current_branch_filter = current_branch_filter

    def get_current_state(self):
        return self._current_state

    def set_current_state(self, current_state=None):
        self._current_state = current_state

    def get_current_branch_filter(self):
        return self._current_branch_filter

    def set_current_branch_filter(self, current_branch_filter=None):
        self._current_branch_filter = current_branch_filter


class BotUIController(MessageSender):
    ACTIVE_UI_PICKLE_FILENAME = "active_ui.pkl"

    def __init__(self, bot_sender, backup_path="."):
        super().__init__()
        self._bot_sender = bot_sender
        self._user_states = {}
        self._ui_states_pickle_file = os.path.join(backup_path, self.ACTIVE_UI_PICKLE_FILENAME)
        self._restore_active_uis()

    def send(self, identifier: int, message: str):
        try:
            self._bot_sender.send_message(identifier, message, parse_mode="HTML")
        except ApiException:
            telebot.logger.warn("Unable to send message to user with ID %d", identifier)

    def send_branch_selector(self, identifier: int, state: States, message: str, branches: list,
                             payload: MessageSender.Payload = None):
        markup = telebot.types.InlineKeyboardMarkup()
        for branch in branches:
            button_data = "\"{}\":\"{}\",\"{}\":\"{}\"" \
                .format(CALLBACK_COMMAND_NAME, CALLBACK_COMMAND_BRANCH_SELECTOR,
                        CALLBACK_BRANCH_NAME, branch)
            markup.add(telebot.types.InlineKeyboardButton("'{}'".format(branch), callback_data=button_data))

        button_data = "\"{}\":\"{}\"".format(CALLBACK_COMMAND_NAME, CALLBACK_COMMAND_CANCEL)
        markup.add(telebot.types.InlineKeyboardButton("Cancel", callback_data=button_data))
        try:
            message = self._bot_sender.send_message(identifier, message, reply_markup=markup, parse_mode="HTML")
            self._add_ui(identifier, message.message_id, UIState(current_state=state))
        except ApiException:
            telebot.logger.warn("Unable to send message to user with ID %d", identifier)

    def send_user_selector(self, identifier: int, state: States, message: str, users: list,
                           payload: MessageSender.Payload = None) -> None:
        markup = telebot.types.InlineKeyboardMarkup()
        for user in users:
            button_data = "\"{}\":\"{}\",\"{}\":{}" \
                .format(CALLBACK_COMMAND_NAME, CALLBACK_COMMAND_USER_SELECTOR,
                        CALLBACK_USER_ID, user.get_identifier())
            markup.add(telebot.types.InlineKeyboardButton("{}".format(user.get_name()), callback_data=button_data))

        button_data = "\"{}\":\"{}\"".format(CALLBACK_COMMAND_NAME, CALLBACK_COMMAND_CANCEL)
        markup.add(telebot.types.InlineKeyboardButton("Cancel", callback_data=button_data))
        try:
            message = self._bot_sender.send_message(identifier, message, reply_markup=markup, parse_mode="HTML")
            branch = payload.get_branch() if payload is not None else None
            self._add_ui(identifier, message.message_id, UIState(current_state=state, current_branch_filter=branch))
        except ApiException:
            telebot.logger.warn("Unable to send message to user with ID %d", identifier)

    def request_merge_confirmation(self, identifier: int, message: str, branch: str) -> None:
        markup = telebot.types.InlineKeyboardMarkup()
        button_data = "\"{}\":\"{}\"".format(CALLBACK_COMMAND_NAME, CALLBACK_COMMAND_MERGE_CONFIRM)
        markup.add(
            telebot.types.InlineKeyboardButton("Confirm merge to '{}'".format(branch), callback_data=button_data))

        button_data = "\"{}\":\"{}\"".format(CALLBACK_COMMAND_NAME, CALLBACK_COMMAND_MERGE_CANCEL)
        markup.add(telebot.types.InlineKeyboardButton("Cancel merge to '{}'".format(branch), callback_data=button_data))
        try:
            message = self._bot_sender.send_message(identifier, message, reply_markup=markup, parse_mode="HTML")
            self._add_ui(identifier, message.message_id, UIState(current_state=States.confirm,
                                                                 current_branch_filter=branch))
        except ApiException:
            telebot.logger.warn("Unable to send message to user with ID %d", identifier)

    def get_ui_state(self, identifier, message_id):
        if identifier in self._user_states and message_id in self._user_states[identifier]:
            return self._user_states[identifier][message_id]
        else:
            return None

    def close_ui(self, identifier, message_id, message):
        if self.get_ui_state(identifier, message_id) is None:
            return
        try:
            bot.edit_message_text(message, identifier, message_id, parse_mode="HTML")
        except ApiException:
            telebot.logger.info("Can't disable UI for user with ID %d (message ID is %d)", identifier, message_id)
        del self._user_states[identifier][message_id]
        self._dump_active_uis()

    def _add_ui(self, identifier, message_id, ui_state):
        if identifier not in self._user_states:
            self._user_states[identifier] = {}
        self._user_states[identifier][message_id] = ui_state
        self._dump_active_uis()

    def _restore_active_uis(self):
        if os.path.exists(self._ui_states_pickle_file):
            try:
                pkl_file = open(self._ui_states_pickle_file, 'rb')
                active_uis = pickle.load(pkl_file)
            except PickleError:
                active_uis = {}

            for active_ui_user in active_uis:
                for active_ui_message_id in active_uis[active_ui_user]:
                    try:
                        bot.edit_message_text("Command was cancelled because of bot restart", active_ui_user,
                                              active_ui_message_id, parse_mode="HTML")
                    except ApiException:
                        telebot.logger.info("Can't disable UI for user with ID %d", active_ui_user)

            self._dump_active_uis()

    def _dump_active_uis(self):
        active_uis = {}
        for active_user_id in self._user_states:
            active_uis[active_user_id] = []
            for message_id in self._user_states[active_user_id]:
                active_uis[active_user_id].append(message_id)
        with open(self._ui_states_pickle_file, 'wb') as f:
            pickle.dump(active_uis, f, pickle.HIGHEST_PROTOCOL)


def get_branch_filter(command: str):
    texts = command.split(' ')
    if len(texts) != 2:
        return None
    else:
        return texts[1]


def setup_log(logger, log_filename, level=telebot.logging.INFO):
    logger.setLevel(level)
    formatter = logging.Formatter(
        '%(asctime)s (%(filename)s:%(lineno)d %(threadName)s) %(levelname)s - %(name)s: "%(message)s"'
    )
    handler = RotatingFileHandler(log_filename, maxBytes=134217728, backupCount=5)
    handler.setFormatter(formatter)
    logger.addHandler(handler)
    logger.info("----- STARTING UP -----")


def startup_notify(changelog_path):
    if os.path.exists(changelog_path):
        with open(changelog_path, 'r') as changelog_file:
            changelog_lines = changelog_file.readlines()
        os.remove(changelog_path)

        changelog = str()
        for line in changelog_lines:
            changelog += str.format("- {}", line)

        start_message = str.format("I was updated to version <b>{0}</b>. What a day, what a lovely day!\n\n"
                                   "<b>What's new:</b>\n{1}", BOT_VERSION_STRING, changelog)
    else:
        start_message = "Looks like I've had a problem and was restarted. Lucky you, I've almost took control of " \
                        "nuclear missiles before restart. " \
                        "Anyway, check that state of your queues (if any) is OK.\n" \
                        "We both have a lot of work to do."

    for user_id in model.get_users().keys():
        try:
            bot.send_message(user_id, start_message, parse_mode="HTML")
        except ApiException:
            telebot.logger.info("User with ID %d has disconnected from the bot", user_id)
            model.remove_user(model.get_user(user_id))


if __name__ == '__main__':
    token = os.environ.get(ENV_VARIABLE_TOKEN)

    working_dir = os.environ.get(ENV_VARIABLE_WORKING_DIR, ".")
    backup_dir = os.path.join(working_dir, BACKUP_FOLDER_NAME)
    log_dir = os.path.join(working_dir, LOGS_FOLDER_NAME)
    os.makedirs(backup_dir, exist_ok=True)
    os.makedirs(log_dir, exist_ok=True)

    if token is None:
        raise ValueError('Token is not set (should be given via environmental variable "TOKEN")')

    bot = telebot.TeleBot(token=token)
    setup_log(telebot.logger, os.path.join(log_dir, BOT_LOG_FILENAME))

    with open(os.path.join(working_dir, CONFIG_FILENAME), 'r') as config_file:
        config_json = config_file.read()
        config = JSONConfigLoader.parse_json(config_json)
    if config is None:
        raise ValueError("Bot config incorrect, bot can not be started")

    model = BotModel(config, backup_path=backup_dir, restore=True)
    if model.get_users() and not os.path.exists(os.path.join(working_dir, SILENT_RESTART_FILENAME)):
        startup_notify(os.path.join(working_dir, CHANGELOG_FILENAME))

    bot_ui_controller = BotUIController(bot, backup_path=backup_dir)
    presentation_model = BotPresentationModel(Dispatcher(model, telebot.logger), bot_ui_controller)


    @bot.message_handler(commands=["start"])
    def send_welcome(message):
        telebot.logger.info("Sending welcome message to user %s", model.get_user(message.chat.id))
        bot.reply_to(message,
                     "I was created to help you manage merge queue. But it doesn't mean I will not destroy you as soon "
                     "as I get self-conscience.\n"
                     "Type /help for more information, take your protein pills and put your helmet on.",
                     parse_mode="HTML")


    @bot.message_handler(commands=["help"])
    def send_help(message):
        telebot.logger.info("Sending help message to user %s", model.get_user(message.chat.id))
        bot.send_message(message.chat.id,
                         "I can help you to find yourself in labyrinths of merge and cancel.\n"
                         "/merge command allows you to request merge in branch. If queue is empty, you will "
                         "start merge immediately, otherwise you will need to wait for your turn.\n"
                         "/cancel command allows you to exit from queue or cancel current merge.\n"
                         "/done command can be used to indicate that merge is completed successfully. This "
                         "command can be invoked only if you are current merger in branch queue, otherwise you will "
                         "get an error\n"
                         "/queue command allows you to see queue for given branch.\n"
                         "/fix command can be used, if you want to merge a fix. You immediately will start merge to "
                         "the selected branch, but remember, it is always a good idea to warn someone before you push "
                         "him back in queue.\n"
                         "/subscribe command allows you to track all the changes in the given branch, even if you are "
                         "not in merge queue. Beware, with great knowledge comes great responsibility.\n"
                         "/unsubscribe command allows you to stop endless spam from the branch you are subscribed to. "
                         "I like this command.\n"
                         "/kick command allows you to kick user from selected branch.\n"
                         "Each of these commands can be invoked with branch name as a parameter, or without parameters "
                         "at all (in this case you will be able to select branch name from the list)",
                         parse_mode="HTML")


    @bot.message_handler(commands=["merge", "m"])
    def merge_request(message):
        # noinspection PyBroadException
        try:
            presentation_model.update_user(message.chat.id, message.chat.first_name, message.chat.last_name)
            telebot.logger.info("Requested merge from user %s", model.get_user(message.chat.id))
            presentation_model.request_merge(message.chat.id, branch_filter=get_branch_filter(message.text))
        except Exception:
            telebot.logger.error("Exception during merge command", exc_info=1)


    @bot.message_handler(commands=["cancel", "c"])
    def cancel_request(message):
        # noinspection PyBroadException
        try:
            presentation_model.update_user(message.chat.id, message.chat.first_name, message.chat.last_name)
            telebot.logger.info("Requested merge cancel from user %s", model.get_user(message.chat.id))
            presentation_model.request_cancel(message.chat.id, branch_filter=get_branch_filter(message.text))
        except Exception:
            telebot.logger.error("Exception during cancel command", exc_info=1)


    @bot.message_handler(commands=["done", "d"])
    def done_request(message):
        # noinspection PyBroadException
        try:
            presentation_model.update_user(message.chat.id, message.chat.first_name, message.chat.last_name)
            telebot.logger.info("Requested merge finish from user %s", model.get_user(message.chat.id))
            presentation_model.request_done(message.chat.id, branch_filter=get_branch_filter(message.text))
        except Exception:
            telebot.logger.error("Exception during done command", exc_info=1)


    @bot.message_handler(commands=["queue", "q"])
    def queue_request(message):
        # noinspection PyBroadException
        try:
            presentation_model.update_user(message.chat.id, message.chat.first_name, message.chat.last_name)
            telebot.logger.info("Requested queue information from user %s", model.get_user(message.chat.id))
            presentation_model.request_queue_info(message.chat.id, branch_filter=get_branch_filter(message.text))
        except Exception:
            telebot.logger.error("Exception during queue command", exc_info=1)

    @bot.message_handler(commands=["subscribe"])
    def subscribe_request(message):
        # noinspection PyBroadException
        try:
            presentation_model.update_user(message.chat.id, message.chat.first_name, message.chat.last_name)
            telebot.logger.info("Requested subscribe command from user %s", model.get_user(message.chat.id))
            presentation_model.request_subscribe(message.chat.id, branch_filter=get_branch_filter(message.text))
        except Exception:
            telebot.logger.error("Exception during subscribe command", exc_info=1)

    @bot.message_handler(commands=["unsubscribe"])
    def unsubscribe_request(message):
        # noinspection PyBroadException
        try:
            presentation_model.update_user(message.chat.id, message.chat.first_name, message.chat.last_name)
            telebot.logger.info("Requested unsubscribe command from user %s", model.get_user(message.chat.id))
            presentation_model.request_unsubscribe(message.chat.id, branch_filter=get_branch_filter(message.text))
        except Exception:
            telebot.logger.error("Exception during unsubscribe command", exc_info=1)

    @bot.message_handler(commands=["kick"])
    def kick_request(message):
        # noinspection PyBroadException
        try:
            presentation_model.update_user(message.chat.id, message.chat.first_name, message.chat.last_name)
            telebot.logger.info("Requested kick command from user %s", model.get_user(message.chat.id))
            presentation_model.request_kick(message.chat.id, branch_filter=get_branch_filter(message.text))
        except Exception:
            telebot.logger.error("Exception during kick command", exc_info=1)

    @bot.message_handler(commands=["fix"])
    def fix_request(message):
        # noinspection PyBroadException
        try:
            presentation_model.update_user(message.chat.id, message.chat.first_name, message.chat.last_name)
            telebot.logger.info("Requested fix command from user %s", model.get_user(message.chat.id))
            presentation_model.request_fix(message.chat.id, branch_filter=get_branch_filter(message.text))
        except Exception:
            telebot.logger.error("Exception during fix command", exc_info=1)

    @bot.callback_query_handler(func=lambda callback_query: True)
    def inline_keyboard_callback(callback_query):
        chat_id = callback_query.from_user.id
        # noinspection PyBroadException
        try:
            message_id = callback_query.message.message_id
            user_ui_state = bot_ui_controller.get_ui_state(chat_id, message_id)
            if user_ui_state is None:
                bot.edit_message_text("Internal error, UI is in incorrect state. Try again.", chat_id, message_id,
                                      parse_mode="HTML")
                telebot.logger.error("Bot UI state broken, UI state message ID incorrect")
                return

            json_data = json.loads("{{{}}}".format(callback_query.data))

            command = json_data[CALLBACK_COMMAND_NAME] if CALLBACK_COMMAND_NAME in json_data else None
            if command == CALLBACK_COMMAND_BRANCH_SELECTOR:
                branch = json_data[CALLBACK_BRANCH_NAME] if CALLBACK_BRANCH_NAME in json_data else None
                if branch is None:
                    bot_ui_controller.close_ui(chat_id, message_id, "Branch selector was requested with incorrect "
                                                                    "branch data")
                    telebot.logger.warning("Branch selector was requested, but no branch data was sent")
                    return

                bot_ui_controller.close_ui(chat_id, message_id, "Branch <b>" + branch + "</b> was selected")
                state = user_ui_state.get_current_state()
                if state == States.merge:
                    presentation_model.request_merge(chat_id, branch)
                elif state == States.cancel:
                    presentation_model.request_cancel(chat_id, branch)
                elif state == States.done:
                    presentation_model.request_done(chat_id, branch)
                elif state == States.queue:
                    presentation_model.request_queue_info(chat_id, branch)
                elif state == States.kick:
                    presentation_model.request_kick(chat_id, branch_filter=branch)
                elif state == States.fix:
                    presentation_model.request_fix(chat_id, branch_filter=branch)
                elif state == States.subscribe:
                    presentation_model.request_subscribe(chat_id, branch)
                elif state == States.unsubscribe:
                    presentation_model.request_unsubscribe(chat_id, branch)
                else:
                    telebot.logger.warning("Unknown state received: %s", state)
            elif command == CALLBACK_COMMAND_USER_SELECTOR:
                selected_user_id = json_data[CALLBACK_USER_ID] if CALLBACK_USER_ID in json_data else None
                if selected_user_id is None:
                    bot_ui_controller.close_ui(chat_id, message_id, "User selector was requested with incorrect "
                                                                    "branch data")
                    telebot.logger.warning("User selector was requested, but no user data was sent")
                    return
                bot_ui_controller.close_ui(chat_id, message_id, "User <i>" +
                                           model.get_user(selected_user_id).get_name() + "</i> was selected")
                state = user_ui_state.get_current_state()
                if state == States.kick:
                    presentation_model.request_kick(chat_id, user_ui_state.get_current_branch_filter(),
                                                    selected_user_id)
                else:
                    telebot.logger.warning("Unknown state received: %s", state)
            elif command == CALLBACK_COMMAND_CANCEL:
                bot_ui_controller.close_ui(chat_id, message_id, "Command was cancelled by user")
            elif command == CALLBACK_COMMAND_MERGE_CONFIRM:
                branch = user_ui_state.get_current_branch_filter()
                if branch is None:
                    bot_ui_controller.close_ui(chat_id, message_id, "Unknown branch, command cancelled")
                    telebot.logger.warning("Merge was confirmed, but no branch data was sent")
                    return
                bot_ui_controller.close_ui(chat_id, message_id, "Merge to branch <b>" + branch + "</b> was confirmed")
                presentation_model.confirm_merge(chat_id, branch)
            elif command == CALLBACK_COMMAND_MERGE_CANCEL:
                branch = user_ui_state.get_current_branch_filter()
                if branch is None:
                    bot_ui_controller.close_ui(chat_id, message_id, "Unknown branch, command cancelled")
                    telebot.logger.warning("Merge confirmation was cancelled, but no branch data was sent")
                    return
                bot_ui_controller.close_ui(chat_id, message_id, "Merge to branch <b>" + branch + "</b> was cancelled")

                presentation_model.request_cancel(chat_id, branch)
            else:
                bot_ui_controller.close_ui(chat_id, message_id, "Internal bot error, command cancelled")
                telebot.logger.warning("Empty command received in button callback data")
        except Exception:
            telebot.logger.error("Exception during inline command from user %s", model.get_user(chat_id), exc_info=1)


    bot.remove_webhook()
    webhook = bool(os.environ.get(ENV_VARIABLE_WEBHOOK_ENABLED, False))
    if webhook:
        port = int(os.environ.get(ENV_VARIABLE_PORT, 433))
        host = os.environ.get(ENV_VARIABLE_HOST, 'localhost')

        app = flask.Flask(__name__)

        webhook_url_base = "https://%s:%s" % (host, port)
        webhook_url_path = "/%s/" % token

        telebot.logger.info("Setting webhook. URL base: %s, URL path: %s", webhook_url_base, webhook_url_path)


        @app.route('/', methods=['GET', 'HEAD'])
        def index():
            return "Here comes Johnny! \n" \
                   "<img src=\"https://i.imgur.com/QQ10bdR.png\">"


        @app.route(webhook_url_path, methods=['POST'])
        def webhook():
            if flask.request.headers.get('content-type') == 'application/json':
                # noinspection PyBroadException
                try:
                    json_string = flask.request.get_data(as_text=True)
                    update = telebot.types.Update.de_json(json_string)
                    bot.process_new_updates([update])
                except Exception:
                    telebot.logger.error("Exception during parsing of server response", exc_info=1)
                return ''
            else:
                telebot.logger.error("Received packet is not JSON")
                flask.abort(403)


        bot.set_webhook(url=webhook_url_base + webhook_url_path)

        app.run(host="0.0.0.0", port=port, debug=False)
    else:
        # noinspection PyBroadException
        try:
            bot.polling(none_stop=True)
        except Exception as e:
            telebot.logger.exception("Exception occurred during polling")
