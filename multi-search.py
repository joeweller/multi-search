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


def get_site_info():
    """Open file and put values into 2 lists"""
    main_list = []
    option_list = []

    try:
        t = open("sites.txt", "r")
        t.close()
    except FileNotFoundError:
        pre_gui_warning_exit("sites.txt not found!", "Please create \"sites.txt\"!")

    with open("sites.txt", "r") as file:
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
                    urls.append([i["name"], i["srch_url"].replace(i["ins_chr"], i["join_chr"].join(search_string))])
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
    main_list, option_list = get_site_info()

    gui = appJar.gui()  # create object

    gui.setSize(300, 120)

    gui.setTitle("Multi-Search")

    # test case for windows vs linux compatibility: icons
    if system_chk() == "Linux":
        gui.setIcon(b_dir + "/icons/linux-icon.gif")
    elif system_chk() == "Windows":
        gui.setIcon(b_dir + "/icons/windows-icon.ico")

    #gui.setLogLevel("critical")  # suppress warnings

    gui.addTickOptionBox("Sites to search", option_list)  # list of sites to search

    gui.setResizable(canResize=False)  # disable resize

    gui.addHorizontalSeparator()

    gui.addValidationEntry("search_field")  # call search_check() when text is changed

    gui.thread(search_check, gui)  # make a thread to check for empty search box

    gui.addMenuCheckBox("Settings", "URL Popup")  # add URL Popup to menu
    gui.setMenuCheckBox("Settings", "URL Popup")  # invert URL Popup (default: true)
    gui.addMenuCheckBox("Settings", "Auto-Open")  # add auto-open feature

    def search_button():
        """Search button calls this on press"""

        selected = gui.getOptionBox("Sites to search")

        s_string = gui.getEntry("search_field")

        s_string = s_string.lower()

        if not s_string:
            gui.warningBox("Empty Search Field", "Nothing to search!", parent=None)
        else:
            urls = make_links(main_list, selected, s_string)

            if gui.getMenuCheckBox("Settings", "Auto-Open"):
                for i in range(len(urls)):
                    if i == 0:
                        webbrowser.open_new(urls[i][1])
                    else:
                        webbrowser.open_new_tab(urls[i][1])

            if gui.getMenuCheckBox("Settings", "URL Popup"):
                gui.startSubWindow("Search URLs", modal=True, blocking=True)  # start setting url window popup
                gui.addLabel("10", "URLs for \"" + s_string + "\"")
                gui.addHorizontalSeparator()

                # add links to window
                for result in urls:
                    gui.addWebLink(result[0], result[1])

                gui.setResizable(canResize=False)

                gui.stopSubWindow()

                gui.showSubWindow("Search URLs")

                gui.destroySubWindow("Search URLs")  # destroy popup window on close

            if not gui.getMenuCheckBox("Settings", "Auto-Open") and not gui.getMenuCheckBox("Settings", "URL Popup"):
                gui.warningBox("No selected output", "Unable to output, please choose under \"settings\"", parent=None)
        return

    gui.addButton("Search!", search_button)

    gui.go()
    del gui
    exit(1)


if __name__ == "__main__":
    main()
