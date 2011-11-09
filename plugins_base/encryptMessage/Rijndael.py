from MainEncryptedMessage import MainEncodeDecode,EntryDialog
import gtk
from __rijndael import rijndaelLib
import base64
import string

class Rijndael(MainEncodeDecode):
    def __init__(self, encryptedMessage):
        ''' Constructor '''
        MainEncodeDecode.__init__(self, encryptedMessage)
        self.gui = RijndaelEncodeDecodeGui()
        password,saveAns = self.showPasswordWindow()
        MainEncodeDecode.setPassword(self, password)
        MainEncodeDecode.setIsSaved(self, saveAns)
        self.en  = RijndaelEncodeDecode(self)
        
    def isEncrypted(self, message):
        ''' verify if it is encrypted '''
        return self.en.isEncrypted(message)
        
    def encode(self, conversation, message):
        ''' encode the message '''
        return self.en.encode(message)
    
    def decode(self, conversation, message):
        ''' decode the message '''
        return self.en.decode(message)
    
    def showPasswordWindow(self):
        ''' Send to UI Show the Password Window '''
        return self.gui.showPasswordWindow()
        
    def changePassword(self):
        ''' Send to UI Show the Password Change Window and update it '''
        password,saveAns = self.gui.showPasswordWindow()
        MainEncodeDecode.setPassword(self, password)
        MainEncodeDecode.setIsSaved(self, True)
        
class RijndaelEncodeDecode():
    def __init__(self, myController):
        ''' Constructor '''
        self.myController = myController
        self.password = None;
        self.rijndael = None;
    
    def createZeros(self, length):
        ''' Create zeros to fill the length of password'''
        zeros = ""
        for i in range(0,length):
                zeros = zeros + '0'
        return zeros;
    
    def fixPassword(self, password):
        ''' add zeros to right of password if it doesn't have 16 or 24 or 32 char'''
        zeros = ''
        lenPassword = len(password)
        if(lenPassword!=16 or lenPassword!=24 or password!=32):          
            if(lenPassword > 32):
                password = password[:32]
            elif(lenPassword > 24):
                length = 32 - len(self.password)
                zeros = self.createZeros(length)
            elif(lenPassword > 16):
                length = 24 - len(self.password)
                zeros = self.createZeros(length)
            else:
                length = 16 - len(self.password)
                zeros = self.createZeros(length)
                
        return password + zeros;
    
    def createRijndael(self):
        ''' create a new instance of rijndael '''
        self.password = self.myController.getPassword();
        self.rijndael = rijndaelLib(self.fixPassword(self.password))
     
    def passwordChanged(self):
        ''' verify if the password changed '''
        if not (self.password == self.myController.getPassword()):
            return True
        return False
            
    def encode(self, message):
        ''' encode '''
        if self.passwordChanged():
            self.createRijndael()
            
        outtxt = ""
        for i in [x*16 for x in range(0, len(message)/16+1)]:
            block = message[i:i+16]
            if len(block) > 0:
                outtxt += self.rijndael.encrypt(string.ljust(block, 16))
                
        return '#$1)3($%' + base64.b64encode(outtxt);
    
    def decode(self, message):
        ''' decode '''
        if self.passwordChanged():
            self.createRijndael()
        message = base64.b64decode(message[8:])
        
        outtxt = ""
        for i in [x*16 for x in range(0, len(message)/16+1)]:
            block = message[i:i+16]
            if len(block) > 0:
                outtxt += self.rijndael.decrypt(string.ljust(block, 16))
        try:
            unicodetext = outtxt.decode('utf-8')
        except: 
            outtxt = _('Not decoded')
        
        return outtxt
    
    def isEncrypted(self, message):
        ''' verify if it's encrypted '''
        if message.startswith("#$1)3($%"):
            return True
        return False
            
class RijndaelEncodeDecodeGui():
    def showPasswordWindow(self):
        ''' Show the password window '''
        win = EntryDialog(_('Please insert the password'), '', modal=gtk.TRUE, visibility=False)
        win.set_title(_('What is your password?'))
        win.show()
        gtk.mainloop()
        return [win.getRet(), win.getSave()]  