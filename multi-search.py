import requests
import os
import sys
from platform import system as system_chk
import appJar
from time import sleep as sleep
from ast import literal_eval
import webbrowser


# check if the script is running inside a bundle
if getattr(sys, 'frozen', False):
        # running in a bundle
        b_dir = sys._MEIPASS
else:
        # running in a normal Python environment
        b_dir = os.path.dirname(os.path.abspath(__file__))


def get_ini_config():
    """examine multi-search.ini and extract take configuration"""
    conf_test = ["urlfile", "auto-open", "show-url"]
    prog_conf = {"urlfile": "", "auto-open": "", "show-url": ""}

    if not os.path.isfile(os.getcwd() + "/multi-search.ini"):
        pre_gui_warning_exit("\"multi-search.ini\" does not exist!\n\nPlease create in multi-search folder.")
    with open(os.getcwd() + "/multi-search.ini") as ini:
        for line in ini:
            if not line.startswith("\n") or line.startswith("\r") or line.startswith("#"):
                _ = line.strip().split("=")
                prog_conf[_[0]] = _[1]

    for c in conf_test:
        if not prog_conf[c]:
            pre_gui_warning_exit("\"multi-search.ini\" Error", "\"multi-search.ini\" does not include either:\n\n\""
                                 + ", ".join(conf_test) + "\"" +
                                 "\n\nPlease add arguments to file.")

    # get bool values for config values
    for a in conf_test[1:3]:

        if prog_conf[a].lower() == "True".lower():
            prog_conf[a] = True
        elif prog_conf[a].lower() == "False".lower():
            prog_conf[a] = False
        else:
            pre_gui_warning_exit("\"multi-search.ini\" error.", "Value for " + a +
                                 "must be either:\n\"True\" or \"False\"")

    return prog_conf


def pre_gui_warning_exit(title, message):
    """Terminal error during init."""
    quit_gui = appJar.gui()

    # test case for windows vs linux compatibility: icons
    if system_chk() == "Linux":
        quit_gui.setIcon(b_dir + "/icons/linux-icon.gif")
    elif system_chk() == "Windows":
        quit_gui.setIcon(b_dir + "/icons/windows-icon.ico")

    quit_gui.warningBox(title, message + "\n\nClose or Press OK to terminate")

    del quit_gui

    sys.exit(0)


def get_site_info(urlfile):
    """Open urlfile and put values into 2 lists"""
    main_list = []
    option_list = []
    urlfile = os.getcwd() + "/" + urlfile

    if not os.path.isfile(urlfile):
        pre_gui_warning_exit("File not found!", "\"" + urlfile +
                             "\" Not found.\n\nPlease create or edit \"multi-search.ini!\"")

    with open(urlfile, "r") as file:
        for line in file:
            if line.startswith("#") or (line.startswith("\n") or line.startswith("\r")):
                continue
            else:
                if line.startswith("-"):
                    line = line.strip()
                    option_list.append(line)
                else:
                    line = line.strip()
                    tmp = literal_eval(line)

                    # test for missing values in dict. exit on search button press for graceful exit
                    for key, val in tmp.items():
                        if not val:
                            pre_gui_warning_exit("Error in sites.txt", "Missing values in:\n\n" +
                                                 str(tmp) +
                                                 "\n\nPlease Fix.")

                    main_list.append(tmp)
                    option_list.append(tmp["name"])
    if len(main_list) == 0:
        pre_gui_warning_exit("sites.txt is empty", "Please add site parameters to \"sites.txt\"")
    return main_list, option_list


def make_links(main_list, selected, search_string):
    """create links from selected sites with search string"""
    urls = []
    search_string = search_string.split(" ")
    for key, val in selected.items():
        if val:  # if true, search for dict entry in main list
            for i in main_list:
                if i["name"] == key:  # found correct dict for ticked box
                    tmp = [i["name"], i["srch_url"].replace(i["ins_chr"], i["join_chr"].join(search_string))]

                    # if json is is not "False" (must be true), get request and create url
                    if not i["json"].lower() == "False".lower():

                        resp = requests.get(tmp[1])  # get request

                        # if dict key is needed; extract data from dict. if not, get response as text
                        if not i["json_dict_key"].lower() == "False".lower():
                            resp = resp.json()
                            resp = resp[i["json_dict_key"]]
                        else:
                            resp = resp.text

                        # check for root URL. if needed, url will be appended to response and added to list
                        if not i["json_req_url_root"].lower() == "False".lower():
                            resp = i["json_req_url_root"] + resp

                        tmp[1] = resp  # return full URL
                    urls.append(tmp)

    return urls


def search_check(gui):
    """function for checking search box. aesthetic"""
    while True:
        if len(gui.getEntry("search_field")) == 0:
            gui.setEntryInvalid("search_field")
        else:
            gui.setEntryValid("search_field")
        sleep(0.2)


def main():
    """Start main window and set params for widgets"""
    ini = get_ini_config()
    main_list, option_list = get_site_info(ini["urlfile"])

    gui = appJar.gui()  # create object

    gui.setSize(300, 120)

    gui.setTitle("multi-search")

    # test case for windows vs linux compatibility: icons
    if system_chk() == "Linux":
        gui.setIcon(b_dir + "/icons/linux-icon.gif")
    elif system_chk() == "Windows":
        gui.setIcon(b_dir + "/icons/windows-icon.ico")

    gui.setLogLevel("critical")  # suppress warnings

    gui.addTickOptionBox("- site select -", option_list)  # list of sites to search

    gui.setResizable(canResize=False)  # disable resize

    gui.addHorizontalSeparator()

    gui.addValidationEntry("search_field")  # call search_check() when text is changed

    gui.thread(search_check, gui)  # make a thread to check for empty search box

    gui.addMenuCheckBox("settings", "URL Popup")  # add URL Popup to menu

    if ini["show-url"]:
        gui.setMenuCheckBox("settings", "URL Popup")  # invert URL Popup to true

    gui.addMenuCheckBox("settings", "Auto-Open")  # add auto-open feature

    if ini["auto-open"]:
        gui.setMenuCheckBox("settings", "Auto-Open")  # invert Auto-Open to true

    def search_button():
        """Search button calls this on press"""

        selected = gui.getOptionBox("- site select -")

        s_string = gui.getEntry("search_field")

        s_string = s_string.lower()

        if not s_string:
            gui.warningBox("Empty Search Field", "Nothing to search!", parent=None)
        else:
            urls = make_links(main_list, selected, s_string)

            if gui.getMenuCheckBox("settings", "Auto-Open"):
                for i in range(len(urls)):
                    if i == 0:
                        webbrowser.open_new(urls[i][1])
                    else:
                        webbrowser.open_new_tab(urls[i][1])

            if gui.getMenuCheckBox("settings", "URL Popup"):
                gui.startSubWindow("search URLs", modal=True, blocking=True)  # start setting url window popup
                gui.addLabel("10", "URLs for \"" + s_string + "\"")
                gui.addHorizontalSeparator()

                # add links to window
                for result in urls:
                    gui.addWebLink(result[0], result[1])

                gui.setResizable(canResize=False)

                gui.stopSubWindow()

                gui.showSubWindow("search URLs")

                gui.destroySubWindow("search URLs")  # destroy popup window on close

            if not gui.getMenuCheckBox("settings", "Auto-Open") and not gui.getMenuCheckBox("settings", "URL Popup"):
                gui.warningBox("No selected output", "Unable to output, please choose under \"settings\"", parent=None)
        return

    gui.addButton("search!", search_button)

    gui.go()
    del gui
    exit(1)


if __name__ == "__main__":
    main()
