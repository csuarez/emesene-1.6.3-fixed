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

from emesenelib import soap, common

def membership(proxy, callback):
    common.debug("soap.requests: membership list", "soap")
    soap.manager.do_request(proxy,
        'http://www.msn.com/webservices/AddressBook/FindMembership',
        'local-bay.contacts.msn.com', 443, '/abservice/SharingService.asmx',
        soap.templates.membershipList, callback)

def address_book(proxy, callback):
    common.debug("soap.requests: address book", "soap")
    soap.manager.do_request(proxy,
        'http://www.msn.com/webservices/AddressBook/ABFindAll',
        'local-bay.contacts.msn.com', 443, '/abservice/abservice.asmx',
        soap.templates.addressBook, callback)

def change_alias(proxy, contactID, alias, callback, *args):
    alias = str(common.escape(alias))
    soap.manager.do_request(proxy,
        'http://www.msn.com/webservices/AddressBook/ABContactUpdate',
        'local-bay.contacts.msn.com', 443, '/abservice/abservice.asmx',
        soap.templates.renameContact % (str(contactID), alias),
        callback, args)

def add_contact(proxy, email, callback, *args):
    soap.manager.do_request(proxy,
        'http://www.msn.com/webservices/AddressBook/ABContactAdd',
        'local-bay.contacts.msn.com', 443, '/abservice/abservice.asmx',
        soap.templates.contactAdd % (email, ), callback, args)

def remove_contact(proxy, contactID, callback, *args):
    soap.manager.do_request(proxy,
        'http://www.msn.com/webservices/AddressBook/ABContactDelete',
        'local-bay.contacts.msn.com', 443, '/abservice/abservice.asmx',
        soap.templates.contactRemove % (contactID, ), callback, args)

def add_to_group(proxy, gid, contactID, callback, *args):
    soap.manager.do_request(proxy,
        'http://www.msn.com/webservices/AddressBook/ABGroupContactAdd',
        'local-bay.contacts.msn.com', 443, '/abservice/abservice.asmx',
        soap.templates.moveUserToGroup % (gid, contactID), callback, args)

def remove_from_group(proxy, contactID, sourceGid, callback, *args):
    soap.manager.do_request(proxy,
        'http://www.msn.com/webservices/AddressBook/ABGroupContactDelete',
        'local-bay.contacts.msn.com', 443, '/abservice/abservice.asmx',
        soap.templates.deleteUserFromGroup % (contactID, sourceGid),
        callback, args)

def add_role(proxy, role, email, callback, *args):
    soap.manager.do_request(proxy,
        'http://www.msn.com/webservices/AddressBook/AddMember',
        'local-bay.contacts.msn.com', 443, '/abservice/SharingService.asmx',
        soap.templates.addMember % (role, email), callback, args)

def delete_role(proxy, role, email, callback, *args):
    soap.manager.do_request(proxy,
        'http://www.msn.com/webservices/AddressBook/DeleteMember',
        'local-bay.contacts.msn.com', 443, '/abservice/SharingService.asmx',
        soap.templates.deleteMember % (role, email), callback, args)

def get_profile(proxy, cid, callback):
    soap.manager.do_request(proxy,
        'http://www.msn.com/webservices/storage/w10/GetProfile',
        'storage.msn.com', 443, '/storageservice/SchematizedStore.asmx',
        soap.templates.getProfile % (cid, ), callback)

def update_profile(proxy, affinityCache, rid, nick, pm, callback, *args):
    soap.manager.do_request(proxy,
        'http://www.msn.com/webservices/storage/w10/UpdateProfile',
        'storage.msn.com', 443, '/storageservice/SchematizedStore.asmx',
        soap.templates.updateProfile % (affinityCache, rid, nick, pm), callback, args)

def create_profile(proxy, callback):
    soap.manager.do_request(proxy,
        'http://www.msn.com/webservices/storage/w10/CreateProfile',
        'storage.msn.com', 443, '/storageservice/SchematizedStore.asmx',
        soap.templates.createProfile, callback)

def update_dp(proxy, affinitycache, cid, name, mimetype, data, callback, *args):
    soap.manager.do_request(proxy,
        'http://www.msn.com/webservices/storage/w10/CreateDocument',
        'storage.msn.com', 443, '/storageservice/SchematizedStore.asmx',
        soap.templates.updateDp % (affinitycache, cid, name, mimetype, data), callback, args)

def create_relationships(proxy, affinitycache, source_id, target_id, callback, *args):
    soap.manager.do_request(proxy,
        'http://www.msn.com/webservices/storage/w10/CreateRelationships',
        'storage.msn.com', 443, '/storageservice/SchematizedStore.asmx',
        soap.templates.createRelationships % (affinitycache, source_id, target_id), callback, args)

def find_document(proxy, affinitycache, cid, callback, *args):
    soap.manager.do_request(proxy,
        'http://www.msn.com/webservices/storage/w10/FindDocuments',
        'storage.msn.com', 443, '/storageservice/SchematizedStore.asmx',
        soap.templates.findDocument % (affinitycache, cid), callback, args)

def delete_relationship1(proxy, affinitycache, dpid, cid, callback, *args):
    soap.manager.do_request(proxy,
        'http://www.msn.com/webservices/storage/w10/DeleteRelationships',
        'storage.msn.com', 443, '/storageservice/SchematizedStore.asmx',
        soap.templates.deleteRelationship1 % (affinitycache, cid, dpid), callback, args)

def delete_relationship2(proxy, affinitycache, dpid, rid, callback, *args):
    soap.manager.do_request(proxy,
        'http://www.msn.com/webservices/storage/w10/DeleteRelationships',
        'storage.msn.com', 443, '/storageservice/SchematizedStore.asmx',
        soap.templates.deleteRelationship2 % (affinitycache, rid, dpid), callback, args)

