#!/usr/bin/env python
# vim: expandtab

import sys
import getopt
import os

if sys.version > '3':
    python2 = os.popen('which python2 2> /dev/null').read().rstrip()
    if python2:
        args = sys.argv[:]
        args.insert(0,python2)
        os.execv(python2,args)
    else:
        sys.exit("%s requires Python Version 2 (python2 not in PATH)" \
            % os.path.basename(__file__))

global Debug
Debug = 0
 
import tempfile

import pygtk
pygtk.require("2.0")
import gobject
import gtk
import gtkunixprint
import cups
import ConfigParser
import locale, gettext

PROGNAME="gnome-manual-duplex"

# edge_config values:
REVERSE = 2
INVERT = 1

# printMode values:
LONGEDGE = 1
SHORTEDGE = 2
BROCHURE = 3

PageSize = [ '', 'a3', 'a4', 'a5', 'b5', 'letter', 'legal', 'tabloid',
             'statement', 'executive', 'folio', 'quarto' ]

#
#       i18n
#
#locale.setlocale(locale.LC_ALL, '')
#locale.bindtextdomain(PROGNAME, DIR)
locale_dir = gettext.bindtextdomain(PROGNAME)   # /usr/share/locale/...
gettext.bindtextdomain(PROGNAME, locale_dir)
gettext.textdomain(PROGNAME)
lang = gettext.translation(PROGNAME, locale_dir, fallback=True)
_ = lang.gettext
gettext.install(PROGNAME, locale_dir)

def usage():
    global Debug
    print("Usage:")
    print("    %s [options] [ps/pdf-file]" % sys.argv[0])
    print("")
    print("gnome-manual-duplex is a utility that adds manual duplex to the")
    print("'Print' menu.  It is a CUPS Virtual Printer as well as  a")
    print(" standalone  utility.  It works with *.ps and *.pdf files.")
    print("")
    print("Options:")
    print("    -D lvl   Set Debug level [%s]" % Debug)
    sys.exit(1)

def load_config(self):
    global Config

    Config = ConfigParser.ConfigParser()
    self.config_path = os.path.expanduser('~/.config/gnome-manual-duplex.cfg')
    try:
        Config.read([self.config_path])
        #print(Config.get('hp1020', 'long_edge_config', 0))
    except:
        return
 
class App(object):       
    def __init__(self):
        global Debug
        global Config

        try:                                
            opts, args = getopt.getopt(sys.argv[1:], "D:", ["debug="])
        except getopt.GetoptError:
            usage()
        for opt, arg in opts:
            if opt == '-D':
                Debug = int(arg)

        builder = gtk.Builder()
        builder.set_translation_domain(PROGNAME)
        ui_file = "gnome-manual-duplex.xml"
        ui_folders = [ '.', '/usr/share/gnome-manual-duplex']
        for ui_folder in ui_folders:
            filename = os.path.join(ui_folder, ui_file)
            if os.path.exists(filename):
                builder.add_from_file(filename)
                break

        #builder.add_from_file("manfeed.xml")
        self.window = builder.get_object("window1")
        self.about = builder.get_object("aboutdialog1")
        self.JobName = builder.get_object("filechooserbutton1")

        if len(args) >= 2:
            usage()
        elif len(args) == 1:
            self.filename = args[0]
            self.JobName.set_filename(args[0])
        else:
            self.filename = ''

        filter = gtk.FileFilter()
        filter.set_name('PS/PDF files')
        filter.add_pattern('*.ps')
        filter.add_pattern('*.pdf')
        filter.add_pattern('application/postscript')
        filter.add_pattern('application/pdf')
        self.JobName.add_filter(filter)
        self.JobName.set_filter(filter)

        filter = gtk.FileFilter()
        filter.set_name('All files')
        filter.add_pattern('*')
        self.JobName.add_filter(filter)

        self.pref = builder.get_object("pref")

        # populate combo_printers
        self.combo_printers = builder.get_object("combo_printers")
        connection = cups.Connection()
        dests = connection.getDests()
        default_printer = connection.getDefault()

        liststore = gtk.ListStore(gobject.TYPE_STRING)
        self.default_index = i = 0
        for (printer, instance) in sorted( dests.keys () ):
            if default_printer == printer:
                self.default_index = i
                extra = " " + _("(default)")
                self.real_default_printer = printer
            else:
                extra = ""
            if printer == "GnomeManualDuplex":
                continue
            if printer == None:
                continue
            if instance != None:
                continue
            liststore.append([printer + extra])
            i = i + 1
        self.combo_printers.set_model(liststore)
        cell = gtk.CellRendererText()
        self.combo_printers.pack_start(cell, True)
        self.combo_printers.add_attribute(cell, 'text', 0)
        self.combo_printers.set_active(self.default_index)
        self.long_edge_reverse = builder.get_object("long_edge_reverse")
        self.long_edge_invert = builder.get_object("long_edge_invert")
        self.short_edge_reverse = builder.get_object("short_edge_reverse")
        self.short_edge_invert = builder.get_object("short_edge_invert")

        self.printdialog = builder.get_object("printdialog1")
        self.evenok = builder.get_object("even-pages-ok")
        self.printMode = LONGEDGE;
        self.SkipOddPages = 0;
        builder.connect_signals(self)
        self.window.show()

        load_config(self)
        self.long_edge_config = REVERSE | INVERT
        self.short_edge_config = REVERSE

        # pagesize
        self.pagesize = builder.get_object("pagesize")
        try:
            pagesize = Config.getint('_gmd_', 'pagesize')
        except:
            pagesize = 0
        # Bug? translatable in glade file doesn't work for ComboBox...
        for x in range(20, -1, -1):
            self.pagesize.remove_text(x)
        for t in _('Default (Use Locale)'), _('A3'), _('A4'), _('A5'), \
            _('B5'), _('Letter'), _('Legal'), _('Tabloid'), _('Statement'), \
            _('Executive'), _('Folio'), _('Quarto'):
            self.pagesize.append_text(t)
        self.pagesize.set_active(pagesize)

    def about_button_clicked_cb(self, widget, data=None):
        response = self.about.run()
        self.about.hide()

    def filechooserbutton1_file_set_cb(self, widget, data=None):
        self.filename = widget.get_filename()

    def gtk_main_quit(self, widget, data=None):
        gtk.main_quit()

    def delete_event(self, widget, data=None):
        gtk.main_quit()
        return False

    def destroy_event(self, widget, data=None):
        gtk.main_quit()

    def pref_cancel_clicked_cb(self, widget, data=None):
        self.pref.hide()

    def pref_cb(self, widget, data=None):
        self.pref.show()
        if self.default_index == self.combo_printers.get_active():
            printer = self.real_default_printer
        else:
            printer = self.combo_printers.get_active_text()     #hp1020
        #print(printer, self.default_index)
        try:
            #print(Config.get(printer, 'long_edge_config'))
            long_edge_config = Config.get(printer, 'long_edge_config')
            short_edge_config = Config.get(printer, 'short_edge_config')
        except:
            long_edge_config = self.long_edge_config
            short_edge_config = self.short_edge_config
            #print('asd')
        self.long_edge_reverse.set_active( (int(long_edge_config) >> 1) & 1)
        self.long_edge_invert.set_active( (int(long_edge_config) >> 0) & 1)
        self.short_edge_reverse.set_active( (int(short_edge_config) >> 1) & 1)
        self.short_edge_invert.set_active( (int(short_edge_config) >> 0) & 1)

    def pagesize_changed_cb(self, widget, data=None):
        Config.remove_section('_gmd_')
        Config.add_section('_gmd_')
        Config.set('_gmd_', 'pagesize', str(self.pagesize.get_active()) )
        configfp = open(self.config_path, 'w')
        Config.write(configfp)

    def combo_printers_changed_cb(self, widget, data=None):
        #print('changed')
        self.pref_cb(self, widget)

    def pref_save_clicked_cb(self, widget, data=None):
        #print(self.combo_printers.get_active())        #18
        if self.default_index == self.combo_printers.get_active():
            printer = self.real_default_printer
        else:
            printer = self.combo_printers.get_active_text()     #hp1020
        #print(printer)
        Config.remove_section(printer)
        Config.add_section(printer)
        long_edge_config = (int(self.long_edge_reverse.get_active() ) << 1) \
                            + int(self.long_edge_invert.get_active() )
        short_edge_config = (int(self.short_edge_reverse.get_active() ) << 1) \
                            + int(self.short_edge_invert.get_active() )
        Config.set(printer, 'long_edge_config', str(long_edge_config))
        Config.set(printer, 'short_edge_config', str(short_edge_config))
        configfp = open(self.config_path, 'w')
        Config.write(configfp)
        #print(self.config_path, self.long_edge_reverse.get_active())
        self.pref.hide()

    def button1_clicked_cb(self, widget, data=None):
        print("clicked")

    def radiobutton1_toggled_cb(self, widget, data=None):
        if widget.get_active():
            self.printMode = LONGEDGE

    def radiobutton2_toggled_cb(self, widget, data=None):
        if widget.get_active():
            self.printMode = SHORTEDGE

    def radiobutton3_toggled_cb(self, widget, data=None):
        if widget.get_active():
            self.printMode = BROCHURE

    def checkbutton1_toggled_cb(self, widget, data=None):
        self.SkipOddPages = not self.SkipOddPages

    def print_cb(self, widget, data=None):
        self.window.hide()
        self.printdialog.show()

    def odd_pages_send_cb(self, widget, data, errormsg):
        return

    def printdialog1_response_cb(self, widget, data=None):
        # print("pclicked" , data)
        if data == gtk.RESPONSE_DELETE_EVENT:
            gtk.main_quit()
        if data == gtk.RESPONSE_CANCEL:
            gtk.main_quit()
        if data == gtk.RESPONSE_OK:
            global title
            self.tempfile = tempfile.NamedTemporaryFile()
            title = os.path.basename(self.filename)
            rc = os.system("file \"" + self.filename + "\" | grep -q PDF")
            if rc == 256:
                self.is_pdf = 0
            else:
                self.is_pdf = 1
            if self.printMode == BROCHURE:
                self.tempfileBrochure = tempfile.NamedTemporaryFile()
                # Convert into brochure
                if self.is_pdf == 1:
                    os.system("pdftops '" + self.filename
                        + "' - | psbook "
                        + " | psnup -2 > "
                        + self.tempfileBrochure.name)
                else:
                    os.system("psbook '" + self.filename
                        + "' | psnup -2 > "
                        + self.tempfileBrochure.name)
                self.filename = self.tempfileBrochure.name
                self.is_pdf = 0 #now converted to ps (if it was not ps already)
            if not self.SkipOddPages:
                # Print out odd pages
                # print(self.filename)
                rc = os.system("file \"" + self.filename + "\" | grep -q PDF")
                print("{ps,pdf}tops '2:0' '" + self.filename + \
                    "' " + self.tempfile.name)
                if self.is_pdf == 1:
                    os.system("pdftops \"" + self.filename
                        + "\" - | pstops 2:0 > "
                        + self.tempfile.name)
                else:
                    os.system("pstops 2:0 \""
                        + self.filename + "\" " + self.tempfile.name)
                # print("is_pdf ", self.is_pdf)
                
                self.printdialog.PrintJob = gtkunixprint.PrintJob(
                    'gmd: odd: ' + title,
                    self.printdialog.get_selected_printer(),
                    self.printdialog.get_settings(),
                    self.printdialog.get_page_setup())
                self.printdialog.PrintJob.set_source_file(self.tempfile.name)
                # self.printdialog.set_manual_capabilities(
                #     gtkunixprint.PRINT_CAPABILITY_GENERATE_PS)
                if Debug == 0:
                    self.printdialog.PrintJob.send(self.odd_pages_send_cb)
                # print("print")
        self.evenok.show()
        self.printdialog.hide()
        self.evenok_clicked = -1;

    def even_cancel_clicked_cb(self, widget, data=None):
        gtk.main_quit()

    def even_ok_clicked_cb(self, widget, data=None):
        global title
        printer = self.printdialog.get_selected_printer()
        if self.printMode == LONGEDGE:
            try:
                config = int( Config.get(printer.get_name(),
                                            'long_edge_config', 0) )
                #print(printer.get_name(), config)
            except:
                config = self.long_edge_config
        else:
            try:
                config = int( Config.get(printer.get_name(),
                                            'short_edge_config', 0) )
            except:
                config = self.short_edge_config
        reverse = [ '1', '-1' ]
        invert = [ '', 'U(1w,1h)' ]
        try:
            pagesize = Config.getint('_gmd_', 'pagesize')
        except:
            pagesize = 0
        if pagesize != 0:
            pagesize = '-p' + PageSize[pagesize]
        else:
            pagesize = ''
        
        print("{ps,pdf}tops " + pagesize + " '2:" + \
            reverse[(config>>1) & 1] + invert[config&1] + "' '" + \
            self.filename + "' " + self.tempfile.name)
        if self.is_pdf == 0:
            os.system("pstops " + pagesize + " '2:" 
                + reverse[(config>>1) & 1] + invert[config&1] + "' '"
                + self.filename + "' " + self.tempfile.name)
        else:
            os.system("pdftops '" + self.filename + "' - | pstops " \
                + pagesize + " '2:" 
                + reverse[(config>>1) & 1] + invert[config&1] + "' "
                + " > " + self.tempfile.name)
        # os.system("cp " + self.tempfile.name + " /tmp/2")
        self.printdialog.PrintJob = gtkunixprint.PrintJob(
            'gmd: even: ' + title,
            self.printdialog.get_selected_printer(),
            self.printdialog.get_settings(),
            self.printdialog.get_page_setup())
        self.printdialog.PrintJob.set_source_file(self.tempfile.name)
        # self.printdialog.set_manual_capabilities(
        #           gtkunixprint.PRINT_CAPABILITY_GENERATE_PS)
        if Debug == 0:
            self.printdialog.PrintJob.send(self.even_pages_send_cb)
        self.evenok.hide()
        self.tempfile.close()

    def even_pages_send_cb(self, widget, data, errormsg):
        gtk.main_quit()
        return

if __name__ == "__main__":
    # print(_('i18n test'))
    app = App()
    gtk.main()
