from MainEncryptedMessage import MainEncodeDecode,EntryDialog
from random import choice
import gtk
import string
import subprocess
import re
import os

try:
    import pexpect
    PEX = True
except:
    PEX = False

class GPG(MainEncodeDecode):
    def __init__(self, encryptedMessage):
        ''' Contructor '''
        if not PEX:
            import dialog
            dialog.error(_('You must install python-pexpect in order to use GPG encode'), \
                None, _('GPG') + ' ' + _('Error'))
            return 
        
        MainEncodeDecode.__init__(self, encryptedMessage)
        self.gui = GPGEncodeDecodeGui()
        self.en  = GPGEncodeDecode(self)
        self.Slash = encryptedMessage.Slash
        self.nameGpg = self.gui.askGPGuser(_('this window'))
        
    def isEncrypted(self, message):
        ''' verify if the message is encrypted '''
        return self.en.isEncrypted(message)
    
        
    def encode(self, conversation, message):
        ''' encode the message '''
        user = conversation.userMail
        if self.nameGpg is None: 
            self.nameGpg = self.gui.askGPGuser(user)
            
        return self.en.encodeText(self.nameGpg, user, message)
           
    def decode(self, conversation, message):
        ''' decode the message '''
        user = conversation.userMail
        return self.en.decodePgp(user, message)
    
    def showPasswordWindow(self):
        ''' Send to UI Show the Password Window '''
        return self.gui.showPasswordWindow()
        
    def changePassword(self):
        ''' Send to UI Show the Password Change Window and update it '''
        password,saveAns = self.gui.showPasswordWindow()
        MainEncodeDecode.setPassword(self, password)
        MainEncodeDecode.setIsSaved(self, True)
            
class GPGEncodeDecodeGui():
    def showPasswordWindow(self):
        ''' Show the password window '''
        win = EntryDialog(_('Please insert your password to decode the message'), '', modal=gtk.TRUE, visibility=False)
        win.set_title(_('What is your password?'))
        win.show()
        gtk.mainloop()
        return [win.getRet(), win.getSave()]  
        
    def askGPGuser(self, email):
        ''' Ask for the name of the user '''
        w = EntryDialog(_('Please insert the name of the GPG user of ' + email + ' that you want to use.'), '', modal=gtk.TRUE, visibility=True)
        w.set_title(_('What is name of the GPG of ' + email))
        w.show()
        gtk.mainloop();
        return w.getRet()
                   
class GPGEncodeDecode():
    
    def __init__(self, myController):
        '''Contructor'''
        self.password = None
        self.myController = myController 
#        self.mainEncodeDecode = myController.MainEncodeDecode
        
    def isEncrypted(self, message):
        ''' Verify if it's a encrypted message '''
        if message.startswith("-----BEGIN PGP MESSAGE-----"):
            return True
        return False
    
    def createRandom(self):
        ''' generate a 8 len string '''
        chars = string.letters + string.digits
        str = ''
        for i in range(8):
            str = str + choice(chars)
        return str
    
    def decodePgp(self, user, message):
        ''' decode the message '''
        fileName = self.createRandom() + '.' + user + '.temp'
        file = open(fileName + '.asc', 'w')
        file.write(message)
        file.close()

        var = pexpect.spawn('gpg -o ' + fileName + ' -d ' + fileName + '.asc')
        var.expect('Enter passphrase:')
        if self.myController.isSaved() is False or self.myController.isPasswordSet() is False: 
            passw,saveAns = self.myController.showPasswordWindow()
            if passw != '' and passw != None:
                var.sendline(passw)
                if saveAns is True:
                    self.myController.setPassword(passw)
                    self.myController.setIsSaved(saveAns)
        else: 
            var.sendline(self.myController.getPassword())
        var.sendline('\r\n')
        
        os.remove(fileName + '.asc')
        if os.path.isfile(fileName):
            file = open(fileName, 'r')
            decodedText = file.read()
            os.remove(fileName);
            return decodedText;
        return _('Not decoded')   
    
    def encodeText(self, nameGpg, user, message):
        ''' encode the text '''
        fileName = self.createRandom() + '.' + user + '.temp'
        file = open(fileName, 'w')
        file.write(message)
        file.close()
        cmd = 'gpg -a -e -r "' + nameGpg + '" ' + fileName
        result = pexpect.run(cmd);
        os.remove(fileName);
        match = re.search('(.*)encryption failed: public key not found(.*)', result)
        if not(match is None):
            return _('Can\'t encrypt it. (Public key not found)')
        file = open(fileName + '.asc', 'r')
        encodedText = file.read()
        os.remove(fileName + '.asc')
        return encodedText