import asyncio
from pywebio import start_server
from pywebio.input import *
from pywebio.output import *
from pywebio.session import defer_call, info as session_info, run_async

chat_msgs = []  # The chat message history. The item is (name, message content)
online_users = set()

async def refresh_msg(my_name):
    """send new message to current session"""
    global chat_msgs
    last_idx = len(chat_msgs)
    while True:
        await asyncio.sleep(0.5)
        for m in chat_msgs[last_idx:]:
            if m[0] != my_name:  
                put_markdown('`%s`: %s' % m, sanitize=True, scope='msg-box')

async def main():
    global chat_msgs

    put_markdown(("## PyWebIO Voxonomy Assistant\nWelcome to the Question Answering Voxonomy service. To use this app press any key + enter to begin recording your question. Then press any key + enter to finish. The Question will display, then an AI Answer will be supplied."))

    put_scrollable(put_scope('msg-box'), height=300, keep_bottom=True)
    nickname = "Intelligent Presenter"
    online_users.add(nickname)

    refresh_task = run_async(refresh_msg(nickname))

    while True:
        data = await input_group(('Recording Cue'), [
            input(name='msg', help_text=('Press any key, then enter to begin recording')),
            actions(name='cmd', buttons=[('Send'), {'label': ('Exit'), 'type': 'cancel'}])
        ], validate=lambda d: ('msg', 'empty point') if d['cmd'] == ('Send') and not d['msg'] else None)
        if data is None:
            break
        put_markdown('`%s`: %s' % (nickname, data['msg']), sanitize=True, scope='msg-box')
        chat_msgs.append((nickname, data['msg']))

    refresh_task.close()
    toast("You have left the chat room")

if __name__ == '__main__':
    start_server(main, debug=True, port=8080)