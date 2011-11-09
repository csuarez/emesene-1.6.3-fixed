# -*- coding: utf-8 -*-

#   This file is part of emesene.
#
#    Emesene is free software; you can redistribute it and/or modify
#    it under the terms of the GNU General Public License as published by
#    the Free Software Foundation; either version 2 of the License, or
#    (at your option) any later version.
#
#    emesene is distributed in the hope that it will be useful,
#    but WITHOUT ANY WARRANTY; without even the implied warranty of
#    MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
#    GNU General Public License for more details.
#
#    You should have received a copy of the GNU General Public License
#    along with emesene; if not, write to the Free Software
#    Foundation, Inc., 51 Franklin St, Fifth Floor, Boston, MA  02110-1301  USA

import gobject
import urllib
import base64
import os
import httplib
import socket
import tempfile
import datetime
import time

import ContactData
import soap.manager
import soap.requests
import soap.templates

import XmlParser

import common

# most contact list management stuff is a mess because
# this wasn't written with msnp13 abstraction in mind
# "msnp13 abstraction" is basically separating
# notification and contact list servers

class ProfileManager(gobject.GObject):
    '''this class has all the methods to
    modify the contacts, groups, nick and stuff
    through SOAP, its made to make Msnp
    more modular, also this class can be
    changed for other implementation later'''

    __gsignals__ = {
        'user-attr-changed' : (gobject.SIGNAL_RUN_LAST, gobject.TYPE_NONE,
            (gobject.TYPE_PYOBJECT,)),
        # olgGroup, newGroup
        'group-attr-changed' : (gobject.SIGNAL_RUN_LAST, gobject.TYPE_NONE,
            (gobject.TYPE_PYOBJECT,gobject.TYPE_PYOBJECT)),
        # email, id, nick, pm, status, alias, blocked
        'contact-added' : (gobject.SIGNAL_RUN_LAST, gobject.TYPE_NONE,
            (gobject.TYPE_PYOBJECT,gobject.TYPE_PYOBJECT,
            gobject.TYPE_PYOBJECT,gobject.TYPE_PYOBJECT,
            gobject.TYPE_PYOBJECT,gobject.TYPE_PYOBJECT,
            gobject.TYPE_PYOBJECT,)),
        # email
        'contact-removed' : (gobject.SIGNAL_RUN_LAST, gobject.TYPE_NONE,
            (gobject.TYPE_PYOBJECT,)),
        # this signal is emited when WE change an attribute on the user
        # the only two attributes that WE can change are alias, and block
        # email, attr_name (block, alias), value
        'contact-attr-changed' : (gobject.SIGNAL_RUN_LAST, gobject.TYPE_NONE,
            (gobject.TYPE_PYOBJECT,gobject.TYPE_PYOBJECT,
                gobject.TYPE_PYOBJECT,)),
        # name, id
        'group-added' : (gobject.SIGNAL_RUN_LAST, gobject.TYPE_NONE,
            (gobject.TYPE_PYOBJECT,gobject.TYPE_PYOBJECT)),
        # name
        'group-removed' : (gobject.SIGNAL_RUN_LAST, gobject.TYPE_NONE,
            (gobject.TYPE_PYOBJECT,)),
        # old_name, new_name
        'group-renamed' : (gobject.SIGNAL_RUN_LAST, gobject.TYPE_NONE,
            (gobject.TYPE_PYOBJECT,gobject.TYPE_PYOBJECT)),
        # contact, group
        'contact-added-to-group' : (gobject.SIGNAL_RUN_LAST, gobject.TYPE_NONE,
            (gobject.TYPE_PYOBJECT,gobject.TYPE_PYOBJECT)),
        # contact, group
        'contact-removed-from-group' : (gobject.SIGNAL_RUN_LAST,
            gobject.TYPE_NONE, (gobject.TYPE_PYOBJECT,gobject.TYPE_PYOBJECT)),
    }

    def __init__(self, config):
        gobject.GObject.__init__(self)
        self.config = config
        self.profile_retrieved = False
        self.rid = ""

    def onGetMembershipList(self, response):
        '''method called when we receive the membership list'''

        if response.status[0] == 200:
            self.setMembershipListXml(response.body)
            self.newCacheFile(self.user + '_ml.xml', response.body)
            #self.emit('user-list-change')

            return True
        else:
            return False

    def onGetAddressBook(self, response):

        if response.status[0] == 200:
            self.newCacheFile(self.user + '_ab.xml', response.body)

            self.setAddressBookXml(response.body)
            self.cid = getCIDFromDynamicItems(response.body)
            self.emit('login-successful')

            return True
        else:
            return False

    def onGetProfile(self, response):
        #print response.body
        if response.status[0] != 200 or \
           response.body.find('<ExpressionProfile>') == -1:
            if self.triedCreatingProfile:
                # we already tried, but failed.. :(
                self.affinityCache = ''
                self.rid = ''
            else:
                #user doesn't have a roaming profile, try create one.
                soap.requests.create_profile(self.proxy, self.reRequestProfile)
            return

        expression_profile = response.body.split('</ExpressionProfile>')[0].split('<ExpressionProfile>')[1]
        self.rid = expression_profile.split('</ResourceID>')[0].split('<ResourceID>')[1]

        try:
            nick = response.body.split('</DisplayName>')[0].split('<DisplayName>')[1]
            nick = common.unescape(nick)
        except:
            nick = ''

        try:
            pm = response.body.split('</PersonalStatus>')[0].split('<PersonalStatus>')[1]
            pm = common.unescape(pm)
        except: 
            pm = ''

        try:
            dpurl = response.body.split('</PreAuthURL>')[0].split('<PreAuthURL>')[1]
        except:
            try:
                dpurl = response.body.split('</StaticUserTilePublicURL>')[0].split('<StaticUserTilePublicURL>')[1]
            except:
                dpurl = ""

        photo = response.body.split('</Photo>')[0].split('<Photo>')[1]
        try:
            self.dpid = photo.split('</ResourceID>')[0].split('<ResourceID>')[1]
        except:
            self.dpid = ''

        try:
            modified = (photo.split('</DateModified>')[0].split('<DateModified>')[1])[0:19]
        except:
            modified = ''

        newAvatar = True
        # compare last avatar date and server avatar date, we can't know
        # the exact time saved on the server, it's something between the
        # time that we sent the request and the time the response arrived
        # that's why I compare with seconds of difference (10 is arbitrary)
        if modified != '':
            serverDate = modified
            savedDate = self.config.user['avatarDate']

            try:
                date1 =  datetime.datetime(int(serverDate[0:4]), \
                         int(serverDate[5:7]), int(serverDate[8:10]), \
                         int(serverDate[11:13]), int(serverDate[14:16]), \
                         int(serverDate[17:19]),0,None)
                date2 =  datetime.datetime(int(savedDate[0:4]), \
                         int(savedDate[5:7]), int(savedDate[8:10]), \
                         int(savedDate[11:13]), int(savedDate[14:16]), \
                         int(savedDate[17:19]),0,None)

                delta = 0
                if date2 > date1:
                    delta = date2 - date1
                else:
                    delta = date1 - date2
                newAvatar = (delta.seconds > 10 or delta.seconds < -10)
            except:
                newAvatar = True

        if dpurl != '' and newAvatar:
            self.config.user['avatarDate'] = modified
            gobject.idle_add(self.getPicture, dpurl)

        self.changeNick(nick, initial=True)
        self.changePersonalMessage(pm)

        #it seems these are not on the response anymore
        try:
            self.affinityCache = response.body.split('</CacheKey>')[0].split('<CacheKey>')[1]
        except:
            self.affinityCache = ''
        try:
            name = photo.split('</Name>')[0].split('<Name>')[1]
        except:
            name = ''

        self.profile_retrieved = True
    
    def updateDisplayPicture(self):
        #if self.affinityCache != '':
        if self.dpid != '':
            soap.requests.delete_relationship1(self.proxy, self.affinityCache, \
                self.dpid, self.cid, self.onDeleteRelationship1)
        else:
            soap.requests.update_dp(self.proxy, self.affinityCache, \
                self.cid, self.config.glob['Id'], 'png', \
                base64.b64encode(self.msnobj.data), self.onCreateRelationships)

    def getPicture(self, url):
        hdrs = {"User-Agent": "MSN Explorer/9.0 (MSN 8.0; TmstmpExt)",}

        if not url.startswith("http://"):
            url = "http://byfiles.storage.msn.com/"+url
        index = url.find("msn.com")
        #remove "http://" and everything after msn.com
        server = url[7:index+7]

        if self.proxy and self.proxy.host != '':
            proxy_connect = 'CONNECT %s:%s HTTP/1.0\r\n'%(self.proxy.host, self.proxy.port)
            user_agent = 'User-Agent: python\r\n'
            if self.proxy.user:
                common.debug('>>> using proxy auth user: '+self.proxy.user)
                # setup basic authentication
                user_pass = base64.encodestring(self.proxy.user+':'+self.proxy.password).replace('\n','')
                proxy_authorization = 'Proxy-authorization: Basic '+user_pass+'\r\n'
                proxy_pieces = proxy_connect+proxy_authorization+user_agent+'\r\n'
            else:
                proxy_pieces = proxy_connect+user_agent+'\r\n'
            # now connect, very simple recv and error checking
            proxy = socket.socket(socket.AF_INET,socket.SOCK_STREAM)
            proxy.connect((self.proxy.host,int(self.proxy.port)))
            proxy.sendall(proxy_pieces)
            response = proxy.recv(8192) 
            status=response.split()[1]
            if status!=str(200):
                raise ValueError,'Error status=%s' % str(status)
                return False
            conn = httplib.HTTPConnection(server, 80)
            conn.sock = proxy
        else:
            conn = httplib.HTTPConnection(server, 80)
        try:
            conn.request("GET", url, headers=hdrs)
            response = conn.getresponse()
        except:
            return
        stat = response.status
        reas = response.reason
        
        if stat != 200:
            # YouFail
            print "failed to download avatar"
            print "reason: ", reas
            return False
        data = response.read()
        #print "DP:", len(data), stat, reas
        fd, fn = tempfile.mkstemp(prefix='emsnpic')
        os.write(fd, data)
        initial = True
        self.emit('self-dp-changed', fn, initial)
        
        return False
 
    def onSetDP(self, response):
        #print 'onSetDP:'+str(response)
        if response.status[0] == 500 and not self.firstSetDpFail:
            self.firstSetDpFail = True
            # delete relationship
            soap.requests.delete_relationship1(self.proxy, self.affinityCache, \
                self.dpid, self.cid, self.onDeleteRelationship1)
        
    def onDeleteRelationship1(self, response):
        #print 'onDelete1:'+str(response)
        #print response.body
        if response.status[0] != 200:
            soap.requests.update_dp(self.proxy, self.affinityCache, self.cid, \
                self.config.glob['Id'], 'png', base64.b64encode(self.msnobj.data), 
                self.onSetDP)
        else:
            soap.requests.delete_relationship2(self.proxy, self.affinityCache, \
                self.dpid, self.rid, self.onDeleteRelationship2)            

    def onDeleteRelationship2(self, response):
        #print 'onDelete2:'+str(response)
        #print response.body
        if response.status[0] == 200:
            soap.requests.update_dp(self.proxy, self.affinityCache, self.cid, \
                self.config.glob['Id'], 'png', base64.b64encode(self.msnobj.data), \
                self.onCreateRelationships)

    def onCreateRelationships(self,response):
        #print 'onCreate:'#+str(response)
        #print response.body
        if response.status[0] == 200:

            # save avatar update time stamp
            aux1 = time.gmtime()
            date = datetime.datetime(aux1[0], aux1[1], aux1[2], aux1[3], \
                              aux1[4], aux1[5])

            # it looks like msn server's are gmt -7                              
            delta = datetime.timedelta(hours=-7)
            date = date + delta

            # make one-digit numbers start with "0"
            year = str(date.year)
            if date.month < 10:
                month = "".join(("0",str(date.month)))
            else:
                month = str(date.month)
            if date.day < 10:
                day = "".join(("0",str(date.day)))
            else:
                day = str(date.day)
            if date.hour < 10:
                hour = "".join(("0",str(date.hour)))
            else:
                hour = str(date.hour)
            if date.minute < 10:
                minutes = "".join(("0",str(date.minute)))
            else:
                minutes = str(date.minute)
            if date.second < 10:
                seconds = "".join(("0",str(date.second)))
            else:
                seconds = str(date.second)

            self.config.user['avatarDate'] = "".join((year,"-",month,"-",day,"T",hour,":",minutes,":",seconds))

            try:
                document_rid = response.body.split('</CreateDocumentResult>')[0].split('<CreateDocumentResult>')[1]
                soap.requests.create_relationships(self.proxy, self.affinityCache, self.rid, \
                    document_rid, self.onFindDocument)
            except:
                pass

    def onFindDocument(self, response):
        #print 'onFind'+str(response)   
        if response.status[0] == 200:
            soap.requests.find_document(self.proxy, self.affinityCache,self.cid,\
                                        self.onEnd)

    def onEnd(self,response):
        #print 'onEnd:'+str(response)
        #print response.body
        try:
            self.dpid = response.body.split('</ResourceID>')[0].split('<ResourceID>')[1]
        except:
            #let the dpid as it was before
            pass

    def reRequestProfile(self, response):
        ''' requests the profile again, after creating it (?) '''
        self.triedCreatingProfile = True
        if response.status[0] == 200:        
            soap.requests.get_profile(self.proxy, self.cid, self.onGetProfile)

    def addUser(self, email, group, *callback_and_args):
        '''add an user to the friend list'''

        if self.contactManager.contact_exists(email):
            # We already have that contact
            return

        self.sendDL('ADL', email, '1')
        self.sendDL('ADL', email, '2')

        # need to add it in prevention of ILN. Don't update user list
        self.contactManager.addNewContact(email)
        soap.requests.add_contact(self.proxy, email, self.onUserAdded, email, \
            group, callback_and_args)

    def onUserAdded(self, response, email, group, *callback_and_args_triple):
        '''this method is called when the addUser soapRequest get a response'''

        common.debug('add user: ' + email + ' ' + str(response.status))

        if response.status[0] == 200:
            # Now that we have the contact id, we show it
            self.contactManager.setContactIdXml(email, response.body)
            guid = response.body.split('<guid>')[1].split('</guid>')[0]
            self.emit('contact-added', email, guid, None, None, 'FLN', None,
                False)

            if group == '':
                self.emit('user-list-change')
            else:
                # once we now the id we can add it to a group
                self.addUserToGroup(email, group)
            if len(callback_and_args_triple[0]) == 3: # alias hack foo(bar, lol)
                func, acco, alias = callback_and_args_triple[0]
                if alias != '':
                    func(acco, alias)
        else:
            self.contactManager.removeContact(email)
            self.emit('user-list-change')
            self.emit('error', 'user-add-error',
                _('User could not be added: %s') % \
                common.parseSoapFault(response))

    def removeUserFromGroup(self, user, group):
        '''remove user from a group'''

        contactID = self.contactManager.getContactId(user)
        sourceGid = self.contactManager.getGroupId(group)

        if sourceGid == '' or sourceGid == 'nogroup':
            return

        self.contactManager.removeUserFromGroup(user, sourceGid)
        self.emit('user-list-change')

        soap.requests.remove_from_group(self.proxy, contactID, sourceGid,
            self.onUserRemovedFromGroup, sourceGid, group, user)

    def onUserRemovedFromGroup(self, response, groupId, group, user):
        common.debug('remove user from group: ' + str(response.status))

        if response.status[0] == 200:
            self.emit('contact-removed-from-group', user, group)
        else:
            self.contactManager.addUserToGroup(user, groupId)
            self.emit('user-list-change')
            self.emit('error', 'user-remove-error', common.parseSoapFault(response))

    def addUserToGroup(self, user, group):
        '''add a user to a group'''

        gid = self.contactManager.getGroupId(group)
        contactID = self.contactManager.getContactId(user)
        if gid == None:
            common.debug('Group not found')
            return
        if gid in self.contactManager.getContact(user).groups:
            common.debug('User already in group')
            return
        if gid == 'nogroup':
            common.debug('Cannot move to no group')
            return

        self.contactManager.addUserToGroup(user, gid)
        self.emit('user-list-change')

        soap.requests.add_to_group(self.proxy, gid, contactID, self.onUserAddedToGroup,
            user, group, gid)

    def onUserAddedToGroup(self, response, user, group, groupId):
        common.debug('add user to group: ' + str(response.status))

        if response.status[0] == 200:
            self.emit('contact-added-to-group', user, group)
        else:
            self.contactManager.removeUserFromGroup(user, groupId)
            self.emit('user-list-change')
            self.emit('error', 'user-add-to-group-error', \
                _('User could not be added to group: %s') % \
                common.parseSoapFault(response))

    def moveUserToGroup(self, user, srcGroup, destGroup, stage=0):
        '''move a user from a group erasing it from de source group'''

        if stage == 0:
            contactID = self.contactManager.getContactId(user)
            sourceGid = self.contactManager.getGroupId(srcGroup)
            destGid = self.contactManager.getGroupId(destGroup)

            # moving to/from No group = adding to destGroup / removing from srcGroup
            if sourceGid == 'nogroup':
                self.addUserToGroup(user, destGroup)
                return
            if destGid == 'nogroup':
                self.removeUserFromGroup(user, srcGroup)
                return

            # check whether or not it's an allowed movement
            if srcGroup == destGroup:
                common.debug('src and dest groups are the same')
                return
            elif self.contactManager.getGroup(destGid).getUser(user) != None:
                common.debug('dest group already contain the user')
                return

            # make the visual changes
            self.contactManager.removeUserFromGroup(user, sourceGid)
            self.contactManager.addUserToGroup(user, destGid)
            self.emit('user-list-change')

            # remove the user from the srcGroup
            soap.requests.remove_from_group(self.proxy, contactID, sourceGid,
                self.onMoveUserToGroup, user, srcGroup, destGroup, 0)

        elif stage == 1:
            gid = self.contactManager.getGroupId(destGroup)
            contactID = self.contactManager.getContactId(user)

            # add the user to the destGroup
            soap.requests.add_to_group(self.proxy, gid, contactID, self.onMoveUserToGroup,
                user, srcGroup, destGroup, 1)

    def onMoveUserToGroup(self, response, user, srcGroup, destGroup, stage):

        common.debug('move user (stage ' + str(stage) + '): ' \
                           + str(response.status))

        status = response.status

        if response.status[0] == 200:
            if stage == 0: # continue the moving procedure
                self.moveUserToGroup(user, srcGroup, destGroup, 1)
        else:
            # restore the old visual
            sourceGid = self.contactManager.getGroupId(srcGroup)
            destGid = self.contactManager.getGroupId(destGroup)

            self.contactManager.removeUserFromGroup(user, destGid)
            self.contactManager.addUserToGroup(user, sourceGid)
            self.emit('user-list-change')
            self.emit('error', 'user-move-to-group-error', _('User could not be moved to group: %s') % common.parseSoapFault(response))

    def removeUser(self, email):
        '''remove an user from the friendr list'''
        self.sendDL('RML', email, '1')

        contact = self.contactManager.getContact(email)
        contactID = self.contactManager.getContactId(email)
        soap.requests.remove_contact(self.proxy, contactID, self.onUserRemoved,
            email, contact)

        # make the contact not visible
        self.contactManager.removeContact(email)
        
    def removeUserFromPending(self, email):
        '''remove an user from the pending list and deny his request'''
        self.sendDL('RML', email, '6')
        
        soap.requests.delete_role(self.proxy, 'Pending', email, \
            self.cb_on_pending_removed, email)

    def cb_on_pending_removed(self, response, email):
        '''called when we have the response'''
        common.debug('remove pending: ' + email + ' ' + str(response.status))

        if response.status[0] != 200:
            self.removeUser(email)
            self.sendDL('RML', email, '6')
            soap.requests.delete_role(self.proxy, 'Pending', email, \
            None, None)
            
    def onUserRemoved(self, response, email, contact):
        '''this method is called when the removeUser soapRequest get a response
        renes means if we have to renew the di,ml,ab data'''

        common.debug('remove user: ' + email + ' ' + str(response.status))

        if response.status[0] == 200:
            self.emit('contact-removed', email)
        else:
            self.sendDL('ADL', email, '1')
            self.contactManager.addContact(contact)

            self.emit('error', 'user-remove-error',
                _('User could not be removed: %s') %
                common.parseSoapFault(response))
        self.emit('user-list-change')

    def blockUser(self, email, stage=0):
        '''block an user'''

        if stage == 0:
            self.sendDL('RML', email, '2')
            self.sendDL('ADL', email, '4')

            self.contactManager.blockContact(email)
            contact = self.contactManager.getContact(email)
            self.emit('user-attr-changed', contact)

            soap.requests.delete_role(self.proxy, 'Allow', email,
                self.onUserBlocked, email, 0)

        elif stage == 1:
            soap.requests.add_role(self.proxy, 'Block', email,
                self.onUserBlocked, email, 1)

    def onUserBlocked(self, response, email, stage):
        '''this method is called when the blockUser soapRequest get a response'''

        common.debug('block user (stage ' + str(stage) + '): ' \
                           + str(response.status))

        if response.status[0] == 200:
            if stage == 0: # continue the blocking process
                self.blockUser(email, 1)

            self.emit('contact-attr-changed', email, 'block', True)
        else:
            self.unblockUser(email, 0)
            self.contactManager.unblockContact(email)
            contact = self.contactManager.getContact(email)
            self.emit('user-attr-changed', contact)

    def unblockUser(self, email, stage=0):
        '''unblock an user'''

        if stage == 0:
            self.sendDL('RML', email, '4')
            self.sendDL('ADL', email, '2')

            self.contactManager.unblockContact(email)
            contact = self.contactManager.getContact(email)
            self.emit('user-attr-changed', contact)

            soap.requests.delete_role(self.proxy, 'Block', email,
                self.onUserUnblocked, email, 0)

        elif stage == 1:
            soap.requests.add_role(self.proxy, 'Allow', email,
                self.onUserUnblocked, email, 1)

    def onUserUnblocked(self, response, email, stage):
        '''this method is called when the unblockUser soapRequest get a response'''

        common.debug('unblock user (stage ' + str(stage) + '): ' \
                           + str(response.status))

        if response.status[0] == 200:
            if stage == 0:
                self.unblockUser(email, 1)

            self.emit('contact-attr-changed', email, 'block', False)
        else:
            self.contactManager.blockContact(email)
            contact = self.contactManager.getContact(email)
            self.emit('user-attr-changed', contact)

    def addGroup(self, group):
        '''add a group to the group list'''

        if self.contactManager.getGroupId(group) != None:
            common.debug('Unable to add: Group "' + group \
                               + '" already exists')
            return

        name = group.replace(' ', '%20')

        soap.manager.do_request(self.proxy,\
            'http://www.msn.com/webservices/AddressBook/ABGroupAdd',
            'contacts.msn.com', 443, '/abservice/abservice.asmx',
            soap.templates.addGroup % (group,),
            self.onGroupAdded, (group,))

    def onGroupAdded(self, response, group):
        '''this method is called when the addGroup soap request get a response'''

        common.debug('add group ' + str(response.status))

        if response.status[0] == 200:
            try:
                gid = response.body.split('<guid>')[1].split('</guid>')[0]
                self.contactManager.addGroup(group, gid)
                self.emit('group-added', group, gid)
                self.emit('user-list-change')
            except IndexError, e:
                common.debug('cannot add group to userlist')
                common.debug(str(e))
        else:
            self.emit('error', 'group-add-error', _('Group could not be added: %s') % common.parseSoapFault(response))

    def removeGroup(self, group):
        '''remove a group from the group list'''

        gid = self.contactManager.getGroupId(group)
        if gid:
            groupObj = self.contactManager.getGroup(gid)
            self.contactManager.removeGroup(gid)
            self.emit('user-list-change')

            soap.manager.do_request(self.proxy,\
                'http://www.msn.com/webservices/AddressBook/ABGroupDelete', \
                'contacts.msn.com', 443, '/abservice/abservice.asmx', \
                soap.templates.deleteGroup % (gid,), \
                self.onGroupRemoved, (gid, groupObj))

        else:
            common.debug('Unable to remove: Group "' + group \
                               + '" does not exist')

    def onGroupRemoved(self, response, gid, group):
        '''this method is called when the removeGroup soap request get a response'''

        common.debug('remove group ' + str(response.status))

        if response.status[0] == 200:
            self.emit('group-removed', group)
        else:
            # TODO: change it to setGroup when it manages contacts
            self.contactManager.setGroup(gid, group)
            self.emit('user-list-change')
            self.emit('error', 'group-remove-error', _('Group could not be removed: %s') % common.parseSoapFault(response))

    def renameGroup(self, oldGroup, newGroup):
        '''rename a group from the group list'''

        if oldGroup == newGroup:
            common.debug('oldgroup and new group are the same')
            return
        if self.contactManager.getGroupId(newGroup) != None:
            common.debug('That group name is already in use')
            return

        gid = self.contactManager.getGroupId(oldGroup)
        if gid == None:
            common.debug('The specified group does not exist')
            return
        else:
            self.contactManager.renameGroup(gid, newGroup)
            group = self.contactManager.getGroup(gid)
            objOldGroup = ContactData.Group(oldGroup)
            self.emit('group-attr-changed', objOldGroup, group)
            soap.manager.do_request(self.proxy,\
                'http://www.msn.com/webservices/AddressBook/ABGroupUpdate', \
                'contacts.msn.com', 443, '/abservice/abservice.asmx', \
                soap.templates.renameGroup % (gid, common.escape(newGroup)), \
                self.onGroupRenamed, (oldGroup, newGroup))

    def onGroupRenamed(self, response, oldGroup, newGroup):
        '''this method is called when the renameGroup soap request get a response'''

        common.debug('rename group ' + str(response.status))

        if response.status[0] == 200:
            self.emit('group-renamed', oldGroup, newGroup)
        else:
            gid = self.contactManager.getGroupId(newGroup)
            self.contactManager.renameGroup(gid, oldGroup)
            group = self.contactManager.getGroup(gid)
            # its old because we revert the changes
            objOldGroup = ContactData.Group(newGroup)
            self.emit('group-attr-changed', objOldGroup, group)
            self.emit('error', 'group-rename-error', _('Group could not be renamed: %s') % common.parseSoapFault(response))

    def changeNick(self, nick, initial=False):
        nick = nick.decode('utf-8', 'replace').encode('utf-8')
        if nick == '':
            nick = self.user

        if not initial and self.nick == nick:
            common.debug('trying to set the same nick')
            return

        if len(nick) > 129:
            # to avoid problems with utf-8
            return

        oldNick = self.nick
        self.nick = nick
        #self.contactManager.setContactNick(self.user, self.nick)
        self.emit('self-nick-changed', oldNick, self.nick)

        self.socket.sendCommand("PRP", "MFN " + urllib.quote(nick))

        if not initial:
            if self.rid != "":# self.affinityCache != '':
                soap.requests.update_profile(self.proxy, self.affinityCache, \
                    self.rid, common.escape(nick), \
                    common.escape(self.personalMessage), self.onNickChanged, oldNick)

    def changeAlias(self, user, alias):
        alias = alias.decode('utf-8', 'replace').encode('utf-8')

        oldAlias = self.contactManager.getContactAlias(user)

        self.contactManager.setContactAlias(user, alias)
        self.emit('user-attr-changed', self.contactManager.getContact(user))

        soap.requests.change_alias(self.proxy, self.contactManager.getContactId(user),
            alias, self.onAliasChanged, user, oldAlias)

    def onNickChanged(self, response, oldNick):
        return # shhht! user exceeded the limit can be bad
        if response.status[0] != 200:
            #self.contactManager.setContactNick(self.user, oldNick)
            self.emit('self-nick-changed', self.nick, oldNick)
            self.emit('error', 'nick-change-error',
                common.parseSoapFault(response))

    def onPmChanged(self, response, oldPm):
        return # shhht! user exceeded the limit can be bad
        if response.status[0] != 200:
            self.emit('self-personal-message-changed', self.personalMessage, oldPm)
            self.emit('error', 'pm-change-error',
                common.parseSoapFault(response))

    def onAliasChanged(self, response, user, oldAlias):
        if response.status[0] != 200:
            self.emit('contact-attr-changed', user, 'alias', oldNick)
            self.contactManager.setContactAlias(user, oldNick)
            contact = self.contactManager.getContact(user)
            self.emit('user-attr-changed', contact)
            self.emit('error', 'nick-change-error',
                common.parseSoapFault(response))

    def updateUUX(self):
        '''update personal message and current media'''
        pm = self.personalMessage
        cm = self.currentMedia
        pm = pm.decode('utf-8', 'replace').encode('utf-8')
        cm = cm.decode('utf-8', 'replace').encode('utf-8')

        self.socket.sendPayloadCommand('UUX', '', \
            '<Data><PSM>' + common.escape(pm) + '</PSM>' + \
            '<CurrentMedia>' + common.escape(cm) + '</CurrentMedia>' + \
            '<MachineGuid></MachineGuid></Data>')

    def changePersonalMessage(self, pm):
        '''change the personal message'''
        if self.personalMessage != pm:
            if len(pm) > 129:
                return
            oldPm = self.personalMessage
            self.personalMessage = pm
            self.updateUUX()
            #if self.affinityCache != '':
            soap.requests.update_profile(self.proxy, self.affinityCache, \
                self.rid, common.escape(self.nick), \
                common.escape(self.personalMessage), self.onPmChanged, oldPm)
            self.emit('self-personal-message-changed', self.user, pm)
        else:
            common.debug("duplicate pm")

    def changeCurrentMedia(self, cm, dict=None):
        '''change the current media'''
        if self.currentMedia != cm:
            self.currentMedia = cm
            self.updateUUX()
            self.emit('self-current-media-changed', self.user, cm, dict)
        else:
            common.debug("duplicate cm")

    def getUserDisplayName(self, mail):
        '''return the user display name or just the mail if it cant be found'''
        mail = mail.lower()
        if mail == self.user:
            return self.nick
        else:
            alias = self.contactManager.getContactAlias(mail)

            if alias:
                return alias
            else:
                return self.contactManager.getContactNick(mail)

    def setAddressBookXml(self, xml):
        '''modify the structure with a new DynamicItems xml'''

        contacts = {}

        for (mail, contact) in self.contactManager.contacts.iteritems():
            contacts[mail] = contact

        self.contactManager.groups = {}
        self.contactManager.noGroup.users = {}
        self.contactManager.contacts = {}

        #doc = minidom.parseString(xml)

        dinamicItems = XmlParser.DynamicParser(xml)
        # Retrieve groups
        for i in dinamicItems.groups:
            groupId = i['groupId']
            name = i['name']

            if groupId not in self.contactManager.groups:
                self.contactManager.setGroup(groupId ,
                    ContactData.Group(name, groupId))
                self.emit('group-added', name, groupId)

        # Retrieve contacts
        for i in dinamicItems.contacts:
            if 'isMessengerUser' in i and 'passportName' in i and \
               i['isMessengerUser'] == 'true':
                # valid
                email = i['passportName'].lower()
                contact = ContactData.Contact(email)
            else:
                continue

            try:
                contactId = i['contactId']
                cid = i['CID']
                contact.id = contactId
                contact.cid = cid

                groups = []

                for guid in i['groupIds']:
                    groups.append(guid)

                contact.groups = groups

                for j in i['Annotations']:
                    try:
                        if j['Name'] == 'AB.NickName':
                            alias = j['Value']
                            contact.alias = urllib.unquote(alias)
                    except:
                        pass

                displayName = i['displayName']
                contact.nick = urllib.unquote(displayName)

                isMobileIMEnabled = i['isMobileIMEnabled']
                contact.mobile = isMobileIMEnabled == 'true'

                hasSpace = i['hasSpace']
                contact.space = hasSpace == 'true'
            except KeyError:
                continue

            if email in contacts:
                contact.status = contacts[email].status
                contact.nick = contacts[email].nick
                contact.personalMessage = contacts[email].personalMessage
                contact.msnobj = contacts[email].msnobj
                contact.clientid = contacts[email].clientid

            # finally adds the contact
            self.contactManager.addContact(contact)
            self.emit('contact-added', contact.email, contact.id, contact.nick,
                contact.personalMessage, contact.status, contact.alias,
                contact.blocked)

            for group_id in contact.groups:
                self.emit('contact-added-to-group', contact.email,
                    self.contactManager.getGroup(group_id).name)

        self.contactManager.updateMemberships()

    def setMembershipListXml(self, xml):
        '''modify the structure with a new MembershipList xml
        if it is the first xml that you send, send first the dynamic items'''

        self.contactManager.lists['Allow'] = []
        self.contactManager.lists['Block'] = []
        self.contactManager.lists['Reverse'] = []
        self.contactManager.lists['Pending'] = []

        #ml = minidom.parseString(xml)
        ml = XmlParser.MembershipParser(xml)

        for i in ml.memberships:
            memberRole = i['MemberRole']

            for j in i['Members']:
                try:
                    email = j['PassportName'].lower()
                    if email not in self.contactManager.lists[memberRole]:
                        self.contactManager.lists[memberRole].append(email)
                    else:
                        pass

                    if memberRole == 'Pending' and 'DisplayName' in j:
                        self.contactManager.pendingNicks[email] = \
                            j['DisplayName']

                except Exception, e:
                    pass

gobject.type_register(ProfileManager)

def getCIDFromDynamicItems(xml):
    try:
        cid = xml.split('<contactType>Me</contactType>')\
                [1].split('</CID>')[0].split('<CID>')[1]
        return cid
    except IndexError:
        return ''

