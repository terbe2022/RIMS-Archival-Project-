"""
box_check.py — confirm the Box app is set up correctly before running anything real.

    python src/box_check.py

Tests each step of the setup in order and tells you exactly which one failed
and how to fix it. Downloads nothing.
"""
from __future__ import annotations

import os
import sys

from dotenv import load_dotenv

OK, FAIL, WARN = "  [ok]  ", "  [FAIL]", "  [warn]"


def main():
    load_dotenv()
    print("\nBox setup check\n" + "=" * 60)

    # ---- 1. credentials present -------------------------------------------
    token = os.getenv("BOX_DEVELOPER_TOKEN")
    need = ["BOX_CLIENT_ID", "BOX_CLIENT_SECRET", "BOX_ENTERPRISE_ID"]
    missing = [k for k in need if not os.getenv(k)]

    if token:
        print(f"{OK} developer token found — testing as your own account")
        print("         valid ~60 min; regenerate in the Developer Console when it expires")
        mode = "token"
    elif missing:
        print(f"{FAIL} no credentials in .env")
        print(f"        missing: {', '.join(missing)}")
        print("\n        Before the admin authorizes the app, the quickest path is a")
        print("        developer token: Developer Console -> your app -> Developer Token")
        print("        -> Generate, then put it in .env as BOX_DEVELOPER_TOKEN.")
        print("        It acts as you, so no Service Account or collaboration is needed.")
        return 1
    else:
        print(f"{OK} client credentials found in .env")
        mode = "ccg"

    folder_id = os.getenv("BOX_ROOT_FOLDER_ID", "318353711369")

    # ---- 2. SDK installed --------------------------------------------------
    try:
        from box_sdk_gen import (BoxClient, BoxCCGAuth, BoxDeveloperTokenAuth,
                                 CCGConfig)
    except ImportError:
        print(f"{FAIL} box-sdk-gen not installed")
        print("        pip install box-sdk-gen")
        return 1
    print(f"{OK} box-sdk-gen installed")

    # ---- 3. can we get a token? -------------------------------------------
    try:
        if mode == "token":
            client = BoxClient(auth=BoxDeveloperTokenAuth(token=token))
        else:
            client = BoxClient(auth=BoxCCGAuth(config=CCGConfig(
                client_id=os.environ["BOX_CLIENT_ID"],
                client_secret=os.environ["BOX_CLIENT_SECRET"],
                enterprise_id=os.environ["BOX_ENTERPRISE_ID"],
            )))
        me = client.users.get_user_me()
    except Exception as e:
        print(f"{FAIL} could not authenticate: {type(e).__name__}: {e}")
        if mode == "token":
            print("\n        Developer tokens last about 60 minutes. Generate a fresh")
            print("        one in the Developer Console and update .env.")
        else:
            print("\n        Most likely causes, in order:")
            print("        1. The app has not been authorized yet — the Status panel")
            print("           should read Authorized, not Not Submitted.")
            print("        2. Client ID or secret copied wrong (watch trailing spaces).")
            print("        3. Enterprise ID confused with Client ID — Enterprise ID is")
            print("           on General Settings.")
        return 1
    print(f"{OK} authenticated")
    print(f"         name:  {getattr(me, 'name', '?')}")
    print(f"         login: {getattr(me, 'login', '?')}")
    print(f"         id:    {getattr(me, 'id', '?')}")

    # ---- 4. can the Service Account see the folder? -----------------------
    try:
        folder = client.folders.get_folder_by_id(folder_id)
    except Exception as e:
        print(f"{FAIL} cannot open folder {folder_id}: {type(e).__name__}")
        if mode == "token":
            print("\n        You are authenticating as yourself, so this means your own")
            print("        account cannot see that folder — check the folder ID.")
            return 1
        print("\n        This is almost always the collaboration step.")
        print("        The Service Account can see nothing until you invite it:")
        print(f"        open the folder in Box -> Share -> Invite People ->")
        print(f"        paste  {getattr(me, 'login', 'the Service Account email')}")
        print("        -> permission Viewer (or Editor if writing back).")
        return 1
    print(f"{OK} folder visible: '{folder.name}' (id {folder_id})")

    # ---- 5. can we list it, and do the fields we need come back? ----------
    try:
        items = client.folders.get_folder_items(
            folder_id, limit=100, usemarker=True,
            fields=["id", "type", "name", "size", "sha1", "extension",
                    "created_at", "modified_at", "path_collection"],
        )
    except Exception as e:
        print(f"{FAIL} cannot list folder contents: {type(e).__name__}: {e}")
        print("        Check that 'Read all files and folders stored in Box'")
        print("        is enabled under Application Scopes, and that the app was")
        print("        re-authorized after any scope change.")
        return 1

    entries = list(items.entries)
    files = [e for e in entries if e.type == "file"]
    folders = [e for e in entries if e.type == "folder"]
    print(f"{OK} listed first page: {len(files)} files, {len(folders)} subfolders")

    if not entries:
        print(f"{WARN} folder appears empty — if it is not, the Service Account")
        print("         may have been invited to a different folder.")
        return 0

    # ---- 6. confirm sha1 is populated (this is what makes triage cheap) ---
    if files:
        f = files[0]
        has_sha1 = bool(getattr(f, "sha1", None))
        print(f"{OK if has_sha1 else WARN} sha1 {'present' if has_sha1 else 'MISSING'} "
              f"on file objects")
        print(f"         sample: {f.name}")
        print(f"           size: {getattr(f, 'size', '?'):,} bytes"
              if getattr(f, "size", None) else "           size: ?")
        print(f"           sha1: {getattr(f, 'sha1', '(none)')}")
        if not has_sha1:
            print("         Without sha1 the free deduplication pass will not work.")

    print("\n" + "=" * 60)
    print("Setup looks good. Next:")
    print(f"  python src/box_inventory.py --folder {folder_id} --out manifest/")
    print("Nothing is downloaded by that step — it builds the manifest from")
    print("metadata alone, which is what makes triage-before-download possible.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
