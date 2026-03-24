import requests
import json
import os

BASE_URL = "http://127.0.0.1:8000/api/"

accounts = {}        # username → session
current_user = None

STORAGE_FILE = "accounts.json"


# ---------- persistence ----------
def save_accounts():
    data = {}

    for user, session in accounts.items():
        data[user] = session.cookies.get_dict()

    with open(STORAGE_FILE, "w") as f:
        json.dump(data, f)


def load_accounts():
    global accounts

    if not os.path.exists(STORAGE_FILE):
        return

    with open(STORAGE_FILE, "r") as f:
        data = json.load(f)

    for user, cookies in data.items():
        s = requests.Session()
        s.cookies.update(cookies)
        accounts[user] = s


def restore_user():
    global current_user

    if accounts:
        current_user = list(accounts.keys())[0]


# ---------- helpers ----------
def handle_response(res):
    try:
        data = res.json()
    except:
        print("Invalid server response.")
        return None

    if res.status_code >= 400:
        print(data.get("error", "Request failed"))
        return None

    return data


def require_login():
    if current_user is None:
        print("Not logged in.")
        return False
    return True


def get_session():
    return accounts.get(current_user)


# ---------- help ----------
def help_cmd():
    print("""
Commands:

Auth:
  register <user> <pass> <pass>
  login <user> <pass>
  logout
  switch <user>
  accounts

Mail:
  inbox
  read <id>
  send <user> <message>
  delete <id>
  clear

Other:
  help
  exit
""")


# ---------- auth ----------
def register(parts):
    if len(parts) < 4:
        print("Usage: register <user> <pass> <pass>")
        return

    user, p1, p2 = parts[1], parts[2], parts[3]

    if p1 != p2:
        print("Passwords do not match.")
        return

    s = requests.Session()

    res = s.post(BASE_URL + "register/", data={
        "username": user,
        "password": p1,
        "confirm_password": p2
    })

    data = handle_response(res)

    if data:
        print(f"User '{user}' created.")


def login(parts):
    global current_user

    if len(parts) < 3:
        print("Usage: login <user> <pass>")
        return

    user, pwd = parts[1], parts[2]

    if user in accounts:
        print("Already logged in. Use switch.")
        return

    s = requests.Session()

    res = s.post(BASE_URL + "login/", data={
        "username": user,
        "password": pwd
    })

    data = handle_response(res)

    if data:
        accounts[user] = s
        current_user = user
        save_accounts()
        print(f"Logged in as {user}")


def logout():
    global current_user

    if not require_login():
        return

    s = get_session()
    s.post(BASE_URL + "logout/")

    print(f"Logged out {current_user}")

    del accounts[current_user]
    current_user = None
    save_accounts()


def switch(parts):
    global current_user

    if len(parts) < 2:
        print("Usage: switch <user>")
        return

    user = parts[1]

    if user not in accounts:
        print("User not logged in.")
        return

    current_user = user
    print(f"Switched to {user}")


def list_accounts():
    if not accounts:
        print("No logged-in users.")
        return

    print("Logged-in users:")

    for user in accounts:
        mark = "*" if user == current_user else ""
        print(f" - {user} {mark}")


# ---------- mail ----------
def inbox():
    if not require_login():
        return

    s = get_session()
    res = s.get(BASE_URL + "inbox/")
    data = handle_response(res)

    if not data:
        return

    mails = data["inbox"]

    if not mails:
        print("Empty inbox.")
        return

    for m in mails:
        status = "R" if m["read"] else "U"
        print(f"{m['id']} | {m['from']} | {status}")
        print(f"  {m['message'][:40]}")


def read(parts):
    if not require_login():
        return

    if len(parts) < 2:
        print("Usage: read <id>")
        return

    s = get_session()
    res = s.get(BASE_URL + f"mail/{parts[1]}/")
    data = handle_response(res)

    if data:
        print(f"\nFrom: {data['from']}")
        print(data["message"])


def send(parts):
    if not require_login():
        return

    if len(parts) < 3:
        print("Usage: send <user> <message>")
        return

    user = parts[1]
    msg = " ".join(parts[2:])

    s = get_session()
    res = s.post(BASE_URL + "send/", data={
        "receiver": user,
        "message": msg
    })

    data = handle_response(res)

    if data:
        print("Sent.")


def delete(parts):
    if not require_login():
        return

    if len(parts) < 2:
        print("Usage: delete <id>")
        return

    s = get_session()
    res = s.delete(BASE_URL + f"mail/{parts[1]}/delete/")
    data = handle_response(res)

    if data:
        print("Deleted.")


def clear():
    if not require_login():
        return

    s = get_session()
    res = s.post(BASE_URL + "clear/")
    data = handle_response(res)

    if data:
        print("Inbox cleared.")


# ---------- main ----------
def main():
    load_accounts()
    restore_user()

    if current_user:
        print(f"Restored session: {current_user}")

    while True:
        try:
            prompt = f"{current_user}> " if current_user else "guest> "
            raw = input(prompt).strip()

            if not raw:
                continue

            parts = raw.split()
            cmd = parts[0]

            if cmd == "exit":
                break
            elif cmd == "help":
                help_cmd()
            elif cmd == "register":
                register(parts)
            elif cmd == "login":
                login(parts)
            elif cmd == "logout":
                logout()
            elif cmd == "switch":
                switch(parts)
            elif cmd == "accounts":
                list_accounts()
            elif cmd == "inbox":
                inbox()
            elif cmd == "read":
                read(parts)
            elif cmd == "send":
                send(parts)
            elif cmd == "delete":
                delete(parts)
            elif cmd == "clear":
                clear()
            else:
                print("Unknown command. Type 'help'.")

        except IndexError:
            print("Missing arguments.")
        except Exception as e:
            print("Error:", str(e))


if __name__ == "__main__":
    main()