from telethon import *
import asyncio
import os,sys
import sqlite3
loop = asyncio.get_event_loop()

session_name = "GMD"
session_file = "{}.session".format(session_name)
output_dir = "Telegram_Backup"
auth_file = "win_auth.dat"

def load_authKey():
    if os.path.exists(auth_file):
        with open(auth_file,"rb") as f:
            authKey = f.read()
        return authKey

    else:
        print("[!] auth.dat NOT FOUND")
        return None

def load_dc():
    if os.path.exists("./dc_conf.dat"):
        with open("dc_conf.dat","r") as f:
            dc = f.read()
        return dc

    else:
        print("[!] dc_conf.dat NOT FOUND")
        return None

def create_session():
    print("[*] CREATE SESSION ...\n")
    conn = sqlite3.connect(session_file)
    c = conn.cursor()

    create_sql = [
        "CREATE TABLE entities(id integer primary key, hash integer not null, username text, phone integer, name text)",
        "CREATE TABLE sent_files (md5_digest blob,file_size integer,type integer,id integer,hash integer,primary key(md5_digest, file_size, type))",
        "CREATE TABLE sessions (dc_id integer primary key,server_address text,port integer,auth_key blob,takeout_id integer)",
        "CREATE TABLE update_state (id integer primary key,pts integer,qts integer,date integer,seq integer)",
        "CREATE TABLE version (version integer primary key)"
    ]

    insert_sql = [
        "INSERT INTO sessions VALUES(?,?,?,?,?)",
        "INSERT INTO version VALUES(6)"
        ]

    dc_id = 5
    dc_address = load_dc() # Find in /data/data/org.telegram.messenger/files/tgnet.dat (dc_conf.dat)
    port = 443
    authkey = load_authKey() # Find in /data/data/org.telegram.messenger/files/tgnet.dat (auth.dat)
    takeout_id = None

    if authkey != None and dc_address != None:
        for i in range(len(create_sql)):
            c.execute(create_sql[i])

        c.execute(insert_sql[0],(dc_id,dc_address,port,authkey,takeout_id,))
        c.execute(insert_sql[1])

        conn.commit()
        conn.close()

        print("[CREATE SESSION DONE]")
        print("[*] CREATE {}.sessions".format(session_name))
        print("[*] DataCenter Address: " + dc_address)
        print("\nPlease start again.\n")

    else:
        conn.close()

def update_session():
    print("[*] UPDATE SESSION ...\n")
    conn = sqlite3.connect(session_file)
    c = conn.cursor()

    dc_sql = "UPDATE sessions SET server_address=?"
    authkey_sql = "UPDATE sessions SET auth_key=?"

    authkey = load_authKey() # Find in /data/data/org.telegram.messenger/files/tgnet.dat (auth.dat)
    dc_address = load_dc() # Find in /data/data/org.telegram.messenger/files/tgnet.dat (dc_conf.dat)

    if authkey != None and dc_address != None:

        c.execute(dc_sql,(dc_address,))
        c.execute(authkey_sql,(authkey,))

        conn.commit()
        conn.close()

        print("[UPDATE SESSION DONE]")
        print("[*] UPDATE {}.sessions".format(session_name))
        print("[*] DataCenter Address: "+dc_address)
        print("\n[!] Please start again.\n")

    else:
        conn.close()

async def init():
    global client
    global username

    if login:
        os.remove(session_file)
        api_id = 1389896
        api_hash = "3db6657ba07ac3571a21ce9e2872b13f"

        client = TelegramClient(session_name,api_id, api_hash)
        phone = input("Input Phone Number (Ex. +821012345678): ")
        await client.start(phone)

        # code = input("> Enter Code (Check SMS or Telegram Messenger): ")
        # await client.sign_in(phone,code)

        user_info = await client.get_me()
        username = user_info.username
        print("[ACCOUNT] "+user_info.first_name + user_info.last_name +"({})".format(username))

    else:
        if os.path.exists(session_file) and os.stat(session_file).st_size :

            # api_id, api_hash create in https://my.telegram.org/
            api_id = 1389896
            api_hash = "3db6657ba07ac3571a21ce9e2872b13f"

            client = await TelegramClient(session_name,api_id, api_hash).start()

            user_info = await client.get_me()
            username = user_info.username
            print("[ACCOUNT] "+user_info.first_name + user_info.last_name +"({})".format(username))

        else:
            print("[!] SESSION NOT FOUND")
            create_session()


async def download_message():
    dialogs = await client.get_dialogs()
    location = ""
    origin_location = os.getcwd()
    create_dir(output_dir)

    print("\n\n######### DOWNLOAD MESSAGE #########")
    print("[Working Directory] " + origin_location + "\n")

    for dialog in dialogs:
        os.chdir(origin_location)

        if dialog.name == "":
            if dialog.entity.phone == None:
                print("")
                print("[UNREGISTERED_USER] " + str(dialog.entity.id))
                create_dir(output_dir+"/"+"UNREGISTERED_USER" + str(dialog.entity.id))
                location = "UNREGISTERED_USER" + str(dialog.entity.id)

            else:
                print("")
                print("[PHONE]" + dialog.entity.phone)
                create_dir(output_dir+"/"+dialog.entity.phone)
                location = dialog.entity.phone
        else:
            print("")
            print("[USER]" + dialog.name)
            create_dir(output_dir+"/"+dialog.name)
            location = dialog.name

        os.chdir(output_dir+"/"+location)
        print("[Download Directory] {base}/{download_dir}".format(base=origin_location, download_dir=output_dir + "/" + location) + "\n")

        file = open(location, "wb")
        try:
            async for message in client.iter_messages(dialog.entity):
                line = "\n\n[{date}]\n{msg}".format(date=message.date, msg=message.text)
                file.write(line.encode('utf-8'))


        except errors.TakeoutInitDelayError as e:
            print('Must wait', e.seconds, 'before takeout')

        except errors.SearchQueryEmptyError as e:
            print("EMPTY")

    print("\n\n######### DOWNLOAD MESSAGE DONE #########")


async def download_media():
    dialogs = await client.get_dialogs()
    location = ""
    origin_location = os.getcwd()
    print("\n\n######### DOWNLOAD MEDIA #########")
    print("[Working Directory] " + origin_location + "\n")

    for dialog in dialogs:
        os.chdir(origin_location)

        if dialog.name == "":
            if dialog.entity.phone == None:
                print("")
                print("[UNREGISTERED_USER] " + str(dialog.entity.id))
                create_dir(output_dir + "/" + "UNREGISTERED_USER" + str(dialog.entity.id))
                location = "UNREGISTERED_USER" + str(dialog.entity.id)

            else:
                print("")
                print("[PHONE]" + dialog.entity.phone)
                create_dir(output_dir + "/" + dialog.entity.phone)
                location = dialog.entity.phone
        else:
            print("")
            print("[USER]" + dialog.name)
            create_dir(output_dir + "/" + dialog.name)
            location = dialog.name

        os.chdir(output_dir + "/" + location)
        print("[Download Directory] {base}/{download_dir}".format(base=origin_location, download_dir=output_dir + "/" + location) + "\n")

        try:
            async for message in client.iter_messages(dialog.entity):
                if message.media != None:
                    media = message.media
                    print("[Download START]")

                    if type(media) == types.MessageMediaContact:
                        file_name = await message.download_media(progress_callback=download_progress, file = "Contact_{}".format(media.phone_number))

                    elif type(media) == types.MessageMediaGeo:
                        geo = media.geo
                        file_name = "Geo_" + str(geo.access_hash)
                        open(file_name,"w").write(str(geo))

                    elif type(media) == types.MessageMediaGeoLive:
                        file_name = await message.download_media(progress_callback=download_progress, file="GeoLive_".format(media.geo))

                    else:
                        file_name = await message.download_media(progress_callback=download_progress)

                    print("[Donwload Done] - {} \n".format(file_name))

                    ### Media Type List ###
                    # MessageMediaContact
                    # MessageMediaDocument
                    # MessageMediaEmpty
                    # MessageMediaGame
                    # MessageMediaGeo
                    # MessageMediaGeoLive
                    # MessageMediaInvoice
                    # MessageMediaPhoto
                    # MessageMediaPoll
                    # MessageMediaUnsupported
                    # MessageMediaVenue
                    # MessageMediaWebPage

        except errors.TakeoutInitDelayError as e:
            print('Must wait', e.seconds, 'before takeout')

        except errors.SearchQueryEmptyError as e:
            print("EMPTY")

    print("\n\n######### DOWNLOAD MEDIA DONE #########")

def download_progress(current, total):
    print("Download {} out of {} Bytes: {:.2%}".format(current, total, current / total))

def create_dir(dir_name):
    try:
        if not os.path.exists(dir_name):
            os.makedirs(dir_name)
    except OSError as e:
        print("ERROR Create Dir: {dir} - {e}".format(dir=dir_name, e=e))

def usage():
    print("\n------------------------------------------\n")
    print("[Usage] {} [Option]\n".format(sys.argv[0]))
    print("--message: Download Text Message")
    print("--media: Download Media Item (Photo, Video, Record ...)")
    print("--update: Update Session (if the session has expired)")

if __name__ == "__main__":
    global login
    login = False
    if len(sys.argv) != 2:
        loop.run_until_complete(init())
        usage()
    else:

        if sys.argv[1] == "--message":
            loop.run_until_complete(init())
            loop.run_until_complete(download_message())
        elif sys.argv[1] == "--media":
            loop.run_until_complete(init())
            loop.run_until_complete(download_media())
        elif sys.argv[1] == "--update":
            update_session()
        elif sys.argv[1] == "--login":
            login = True
            loop.run_until_complete(init())
        else:
            usage()