import gtk

class MainEncodeDecode():
    
    def __init__(self, encryptedMessage):
        ''' constructor '''
        self.password = None
        self.saveAns = False
        self.encryptedMessage = encryptedMessage
    
    def isSaved(self):
        ''' return if password is saved '''
        return self.saveAns
    
    def setPassword(self, password):
        ''' set Password '''
        self.password = password
        
    def setIsSaved(self, saveAns):
        ''' set saveAns '''
        self.saveAns = saveAns

    def isPasswordSet(self):
        ''' return if the password is set '''
        if self.password != None and self.password != '':
            return True
        return False

    def getPassword(self):
        ''' return the password '''
        return self.password
    
class EntryDialog(gtk.Dialog):
    def __init__(self, message="", default_text='', modal= gtk.TRUE, visibility=True):
        gtk.Dialog.__init__(self)
        self.set_position(gtk.WIN_POS_CENTER)
        self.saveAns = False
        self.connect("destroy", self.quit)
        self.connect("delete_event", self.quit)
        if modal:
            self.set_modal(gtk.TRUE)
        box = gtk.VBox(spacing=10)
        box.set_border_width(10)
        self.vbox.pack_start(box)
        box.show()
        if message:
            label = gtk.Label(message)
            box.pack_start(label)
            label.show()
            
        self.entry = gtk.Entry()
        self.entry.set_visibility(visibility)
        self.entry.set_text(default_text)
        box.pack_start(self.entry)
        self.entry.show()
        self.entry.grab_focus()
        button = gtk.Button(_("OK"))
        button.connect("clicked", self.click)
        button.set_flags(gtk.CAN_DEFAULT)
        self.action_area.pack_start(button)
        button.show()
        button.grab_default()
        
        button = gtk.Button(_("Save"))
        button.connect("clicked", self.save)
        button.set_flags(gtk.CAN_DEFAULT)
        self.action_area.pack_start(button)
        button.show()
        
        
        button = gtk.Button(_("Cancel"))
        button.connect("clicked", self.quit)
        button.set_flags(gtk.CAN_DEFAULT)
        self.action_area.pack_start(button)
        button.show()
        
        self.ret = None
    def quit(self, w=None, event=None):
        self.hide()
        self.destroy()
        gtk.mainquit()
    def click(self, button):
        self.ret = self.entry.get_text()
        self.quit()
    def save(self, button):
        self.ret = self.entry.get_text()
        self.saveAns = True
        self.quit()
    def getRet(self):
        return self.ret
    def getSave(self):
        return self.saveAns