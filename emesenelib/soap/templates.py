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


# userName, passport, ticket
passport ='''<?xml version="1.0" encoding="UTF-8"?>
<Envelope xmlns="http://schemas.xmlsoap.org/soap/envelope/" xmlns:wsse="http://schemas.xmlsoap.org/ws/2003/06/secext" xmlns:saml="urn:oasis:names:tc:SAML:1.0:assertion" xmlns:wsp="http://schemas.xmlsoap.org/ws/2002/12/policy" xmlns:wsu="http://docs.oasis-open.org/wss/2004/01/oasis-200401-wss-wssecurity-utility-1.0.xsd" xmlns:wsa="http://schemas.xmlsoap.org/ws/2004/03/addressing" xmlns:wssc="http://schemas.xmlsoap.org/ws/2004/04/sc" xmlns:wst="http://schemas.xmlsoap.org/ws/2004/04/trust">
  <Header>
    <ps:AuthInfo xmlns:ps="http://schemas.microsoft.com/Passport/SoapServices/PPCRL" Id="PPAuthInfo">
           <ps:HostingApp>{7108E71A-9926-4FCB-BCC9-9A9D3F32E423}</ps:HostingApp>
           <ps:BinaryVersion>4</ps:BinaryVersion>
           <ps:UIVersion>1</ps:UIVersion>
           <ps:Cookies></ps:Cookies>
           <ps:RequestParams>AQAAAAIAAABsYwQAAAAxMDMz</ps:RequestParams>
       </ps:AuthInfo>
    <wsse:Security>
       <wsse:UsernameToken Id="user">
         <wsse:Username>%s</wsse:Username> 
         <wsse:Password>%s</wsse:Password>
       </wsse:UsernameToken>
    </wsse:Security>
  </Header>
  <Body>

    <ps:RequestMultipleSecurityTokens xmlns:ps="http://schemas.microsoft.com/Passport/SoapServices/PPCRL" Id="RSTS">
      <wst:RequestSecurityToken Id="RST0">
        <wst:RequestType>http://schemas.xmlsoap.org/ws/2004/04/security/trust/Issue</wst:RequestType>
        <wsp:AppliesTo>
          <wsa:EndpointReference>				
            <wsa:Address>http://Passport.NET/tb</wsa:Address>
          </wsa:EndpointReference>
        </wsp:AppliesTo>
      </wst:RequestSecurityToken>
      <wst:RequestSecurityToken Id="RST1">
        <wst:RequestType>http://schemas.xmlsoap.org/ws/2004/04/security/trust/Issue</wst:RequestType>
        <wsp:AppliesTo>
          <wsa:EndpointReference>
            <wsa:Address>messengerclear.live.com</wsa:Address>
          </wsa:EndpointReference>
        </wsp:AppliesTo>
        <wsse:PolicyReference URI="MBI_KEY_OLD"></wsse:PolicyReference>
      </wst:RequestSecurityToken>
        <wst:RequestSecurityToken Id="RST2">
            <wst:RequestType>http://schemas.xmlsoap.org/ws/2004/04/security/trust/Issue</wst:RequestType>
                <wsp:AppliesTo>
                    <wsa:EndpointReference>
                    <wsa:Address>messenger.msn.com</wsa:Address>
                </wsa:EndpointReference>
            </wsp:AppliesTo>
            <wsse:PolicyReference URI="?id=507"></wsse:PolicyReference>
        </wst:RequestSecurityToken>
        <wst:RequestSecurityToken Id="RST3">
            <wst:RequestType>http://schemas.xmlsoap.org/ws/2004/04/security/trust/Issue</wst:RequestType>
            <wsp:AppliesTo>
                <wsa:EndpointReference>
                    <wsa:Address>local-sn.contacts.msn.com</wsa:Address>
                </wsa:EndpointReference>
            </wsp:AppliesTo>
            <wsse:PolicyReference URI="MBI"></wsse:PolicyReference>
        </wst:RequestSecurityToken>
        <wst:RequestSecurityToken Id="RST4">
            <wst:RequestType>http://schemas.xmlsoap.org/ws/2004/04/security/trust/Issue</wst:RequestType>
            <wsp:AppliesTo>
                <wsa:EndpointReference>
                    <wsa:Address>messengersecure.live.com</wsa:Address>
                </wsa:EndpointReference>
            </wsp:AppliesTo>
            <wsse:PolicyReference URI="MBI_SSL"></wsse:PolicyReference>
        </wst:RequestSecurityToken>
<wst:RequestSecurityToken Id="RST5">
<wst:RequestType>http://schemas.xmlsoap.org/ws/2004/04/security/trust/Issue</wst:RequestType>
<wsp:AppliesTo>
<wsa:EndpointReference>
<wsa:Address>storage.msn.com</wsa:Address>
</wsa:EndpointReference>
</wsp:AppliesTo>
<wsse:PolicyReference URI="MBI">
</wsse:PolicyReference>
</wst:RequestSecurityToken>
    </ps:RequestMultipleSecurityTokens>
  </Body>
</Envelope>'''

membershipList = '''<?xml version='1.0' encoding='utf-8'?>
<soap:Envelope xmlns:soap="http://schemas.xmlsoap.org/soap/envelope/">
   <soap:Header xmlns:soap="http://schemas.xmlsoap.org/soap/envelope/">
       <ABApplicationHeader xmlns="http://www.msn.com/webservices/AddressBook">
           <ApplicationId xmlns="http://www.msn.com/webservices/AddressBook">CFE80F9D-180F-4399-82AB-413F33A1FA11</ApplicationId>
           <IsMigration xmlns="http://www.msn.com/webservices/AddressBook">false</IsMigration>
           <PartnerScenario xmlns="http://www.msn.com/webservices/AddressBook">Initial</PartnerScenario>
       </ABApplicationHeader>
       <ABAuthHeader xmlns="http://www.msn.com/webservices/AddressBook">
           <ManagedGroupRequest xmlns="http://www.msn.com/webservices/AddressBook">false</ManagedGroupRequest>
           <TicketToken>&tickettoken;</TicketToken>
       </ABAuthHeader>
   </soap:Header>
   <soap:Body xmlns:soap="http://schemas.xmlsoap.org/soap/envelope/">
       <FindMembership xmlns="http://www.msn.com/webservices/AddressBook">
           <serviceFilter xmlns="http://www.msn.com/webservices/AddressBook">
               <Types xmlns="http://www.msn.com/webservices/AddressBook">
                   <ServiceType xmlns="http://www.msn.com/webservices/AddressBook">Messenger</ServiceType>
               </Types>
           </serviceFilter>
           <View xmlns="http://www.msn.com/webservices/AddressBook">Full</View>
        </FindMembership>
   </soap:Body>
</soap:Envelope>\r\n'''

addressBook = '''<?xml version="1.0" encoding="utf-8"?>
<soap:Envelope xmlns:soap="http://schemas.xmlsoap.org/soap/envelope/" xmlns:xsi="http://www.w3.org/2001/XMLSchema-instance" xmlns:xsd="http://www.w3.org/2001/XMLSchema" xmlns:soapenc="http://schemas.xmlsoap.org/soap/encoding/">
    <soap:Header>
        <ABApplicationHeader xmlns="http://www.msn.com/webservices/AddressBook">
            <ApplicationId>CFE80F9D-180F-4399-82AB-413F33A1FA11</ApplicationId>
            <IsMigration>false</IsMigration>
            <PartnerScenario>Initial</PartnerScenario>
        </ABApplicationHeader>
        <ABAuthHeader xmlns="http://www.msn.com/webservices/AddressBook">
            <ManagedGroupRequest>false</ManagedGroupRequest>
            <TicketToken>&tickettoken;</TicketToken>
        </ABAuthHeader>
    </soap:Header>
    <soap:Body>
        <ABFindAll xmlns="http://www.msn.com/webservices/AddressBook">
            <abId>00000000-0000-0000-0000-000000000000</abId>
            <abView>Full</abView>
            <lastChange>0001-01-01T00:00:00.0000000-08:00</lastChange>
        </ABFindAll>
    </soap:Body>
</soap:Envelope>\r\n'''

# the first parameter Should be replaced with the group  ID
# the secont parameter should specify the member by contactId
# POST /abservice/abservice.asmx HTTP/1.1
# SOAPAction: http://www.msn.com/webservices/AddressBook/ABGroupContactAdd
# Host: omega.contacts.msn.com

oldaddUserToGroup =  '''<?xml version="1.0" encoding="utf-8"?>
<soap:Envelope xmlns:soap="http://schemas.xmlsoap.org/soap/envelope/"
xmlns:xsi="http://www.w3.org/2001/XMLSchema-instance"
xmlns:xsd="http://www.w3.org/2001/XMLSchema"
xmlns:soapenc="http://schemas.xmlsoap.org/soap/encoding/">'
<soap:Header>
  <ABApplicationHeader xmlns="http://www.msn.com/webservices/AddressBook">
    <ApplicationId>CFE80F9D-180F-4399-82AB-413F33A1FA11</ApplicationId>
    <IsMigration>false</IsMigration>
    <PartnerScenario>Timer</PartnerScenario>
  </ABApplicationHeader>
  <ABAuthHeader xmlns="http://www.msn.com/webservices/AddressBook">
    <ManagedGroupRequest>false</ManagedGroupRequest>
    <TicketToken>&tickettoken;</TicketToken>
  </ABAuthHeader>
</soap:Header>
<soap:Body>
  <ABGroupContactAdd xmlns="http://www.msn.com/webservices/AddressBook">
    <abId>00000000-0000-0000-0000-000000000000</abId>
    <groupFilter>
      <groupIds>
        <guid>%s</guid>
      </groupIds>
    </groupFilter>
    <contacts>
      <Contact>
        <contactId>%s</contactId>
      </Contact>
    </contacts>
  </ABGroupContactAdd>
</soap:Body>
</soap:Envelope>\r\n'''

moveUserToGroup = '''<?xml version="1.0" encoding="utf-8"?><soap:Envelope xmlns:soap="http://schemas.xmlsoap.org/soap/envelope/" xmlns:xsi="http://www.w3.org/2001/XMLSchema-instance" xmlns:xsd="http://www.w3.org/2001/XMLSchema" xmlns:soapenc="http://schemas.xmlsoap.org/soap/encoding/">
<soap:Header><ABApplicationHeader xmlns="http://www.msn.com/webservices/AddressBook"><ApplicationId>CFE80F9D-180F-4399-82AB-413F33A1FA11</ApplicationId><IsMigration>false</IsMigration><PartnerScenario>Timer</PartnerScenario></ABApplicationHeader>
<ABAuthHeader xmlns="http://www.msn.com/webservices/AddressBook"><ManagedGroupRequest>false</ManagedGroupRequest><TicketToken>&tickettoken;</TicketToken></ABAuthHeader></soap:Header>
<soap:Body><ABGroupContactAdd xmlns="http://www.msn.com/webservices/AddressBook"><abId>00000000-0000-0000-0000-000000000000</abId><groupFilter><groupIds><guid>%s</guid></groupIds></groupFilter><contacts><Contact><contactId>%s</contactId></Contact></contacts></ABGroupContactAdd></soap:Body></soap:Envelope>'''

# contactID and guid
deleteUserFromGroup = '''<?xml version="1.0" encoding="utf-8"?><soap:Envelope xmlns:soap="http://schemas.xmlsoap.org/soap/envelope/" xmlns:xsi="http://www.w3.org/2001/XMLSchema-instance" xmlns:xsd="http://www.w3.org/2001/XMLSchema" xmlns:soapenc="http://schemas.xmlsoap.org/soap/encoding/">
<soap:Header><ABApplicationHeader xmlns="http://www.msn.com/webservices/AddressBook"><ApplicationId>CFE80F9D-180F-4399-82AB-413F33A1FA11</ApplicationId><IsMigration>false</IsMigration><PartnerScenario>Timer</PartnerScenario></ABApplicationHeader>
<ABAuthHeader xmlns="http://www.msn.com/webservices/AddressBook"><ManagedGroupRequest>false</ManagedGroupRequest><TicketToken>&tickettoken;</TicketToken></ABAuthHeader></soap:Header>
<soap:Body><ABGroupContactDelete xmlns="http://www.msn.com/webservices/AddressBook"><abId>00000000-0000-0000-0000-000000000000</abId><contacts><Contact><contactId>%s</contactId></Contact></contacts><groupFilter><groupIds><guid>%s</guid></groupIds></groupFilter></ABGroupContactDelete></soap:Body></soap:Envelope>'''

addUserToGroup = '''<?xml version="1.0" ?>
<soap:Envelope xmlns:soap="http://schemas.xmlsoap.org/soap/envelope/" xmlns:soapenc="http://schemas.xmlsoap.org/soap/encoding/" xmlns:xsd="http://www.w3.org/2001/XMLSchema" xmlns:xsi="http://www.w3.org/2001/XMLSchema-instance">
<soap:Header><ABApplicationHeader xmlns="http://www.msn.com/webservices/AddressBook"><ApplicationId>CFE80F9D-180F-4399-82AB-413F33A1FA11</ApplicationId><IsMigration>false</IsMigration><PartnerScenario>BlockUnblock</PartnerScenario></ABApplicationHeader>
<ABAuthHeader xmlns="http://www.msn.com/webservices/AddressBook"><ManagedGroupRequest>false</ManagedGroupRequest><TicketToken>&tickettoken;</TicketToken></ABAuthHeader></soap:Header>
<soap:Body>
<ABGroupContactAdd xmlns="http://www.msn.com/webservices/AddressBook">
<abId>00000000-0000-0000-0000-000000000000</abId>
<groupFilter><groupIds><guid>%s</guid></groupIds></groupFilter>
<contacts><Contact xmlns="http://www.msn.com/webservices/AddressBook"><contactInfo><passportName>%s</passportName><isSmtp>false</isSmtp><isMessengerUser>true</isMessengerUser></contactInfo></Contact></contacts>
<groupContactAddOptions><fGenerateMissingQuickName>true</fGenerateMissingQuickName></groupContactAddOptions>
</ABGroupContactAdd>
</soap:Body></soap:Envelope>'''

# contactID nick
renameContact = '''<?xml version="1.0" encoding="utf-8"?><soap:Envelope xmlns:soap="http://schemas.xmlsoap.org/soap/envelope/" xmlns:xsi="http://www.w3.org/2001/XMLSchema-instance" xmlns:xsd="http://www.w3.org/2001/XMLSchema" xmlns:soapenc="http://schemas.xmlsoap.org/soap/encoding/">
<soap:Header><ABApplicationHeader xmlns="http://www.msn.com/webservices/AddressBook"><ApplicationId>CFE80F9D-180F-4399-82AB-413F33A1FA11</ApplicationId><IsMigration>false</IsMigration><PartnerScenario>Timer</PartnerScenario></ABApplicationHeader>
<ABAuthHeader xmlns="http://www.msn.com/webservices/AddressBook"><ManagedGroupRequest>false</ManagedGroupRequest><TicketToken>&tickettoken;</TicketToken></ABAuthHeader></soap:Header>
<soap:Body><ABContactUpdate xmlns="http://www.msn.com/webservices/AddressBook"><abId>00000000-0000-0000-0000-000000000000</abId>
<contacts><Contact xmlns="http://www.msn.com/webservices/AddressBook"><contactId>%s</contactId><contactInfo><annotations><Annotation><Name>AB.NickName</Name><Value>%s</Value></Annotation></annotations></contactInfo><propertiesChanged>Annotation </propertiesChanged></Contact></contacts>
</ABContactUpdate></soap:Body></soap:Envelope>'''

# the first %s is Allow or Block, the second is the passport mail
# POST /abservice/SharingService.asmx HTTP/1.1
# SOAPAction: http://www.msn.com/webservices/AddressBook/AddMember
# Host: omega.contacts.msn.com
addMember='''<?xml version="1.0" encoding="utf-8"?><soap:Envelope xmlns:soap="http://schemas.xmlsoap.org/soap/envelope/" xmlns:xsi="http://www.w3.org/2001/XMLSchema-instance" xmlns:xsd="http://www.w3.org/2001/XMLSchema" xmlns:soapenc="http://schemas.xmlsoap.org/soap/encoding/">
<soap:Header><ABApplicationHeader xmlns="http://www.msn.com/webservices/AddressBook"><ApplicationId>CFE80F9D-180F-4399-82AB-413F33A1FA11</ApplicationId><IsMigration>false</IsMigration><PartnerScenario></PartnerScenario></ABApplicationHeader>
<ABAuthHeader xmlns="http://www.msn.com/webservices/AddressBook"><ManagedGroupRequest>false</ManagedGroupRequest><TicketToken>&tickettoken;</TicketToken></ABAuthHeader></soap:Header>
<soap:Body><AddMember xmlns="http://www.msn.com/webservices/AddressBook"><serviceHandle><Id>0</Id><Type>Messenger</Type><ForeignId></ForeignId></serviceHandle><memberships><Membership><MemberRole>%s</MemberRole><Members><Member xsi:type="PassportMember" xmlns:xsi="http://www.w3.org/2001/XMLSchema-instance"><Type>Passport</Type><State>Accepted</State><PassportName>%s</PassportName></Member></Members></Membership></memberships></AddMember></soap:Body></soap:Envelope>'''

contactAdd = '''<?xml version="1.0" encoding="utf-8"?><soap:Envelope xmlns:soap="http://schemas.xmlsoap.org/soap/envelope/"   xmlns:xsi="http://www.w3.org/2001/XMLSchema-instance" xmlns:xsd="http://www.w3.org/2001/XMLSchema" xmlns:soapenc="http://schemas.xmlsoap.org/soap/encoding/">
<soap:Header><ABApplicationHeader xmlns="http://www.msn.com/webservices/AddressBook"><ApplicationId>CFE80F9D-180F-4399-82AB-413F33A1FA11</ApplicationId><IsMigration>false</IsMigration><PartnerScenario>ContactSave</PartnerScenario></ABApplicationHeader>
<ABAuthHeader xmlns="http://www.msn.com/webservices/AddressBook"><ManagedGroupRequest>false</ManagedGroupRequest><TicketToken>&tickettoken;</TicketToken></ABAuthHeader></soap:Header>
<soap:Body><ABContactAdd xmlns="http://www.msn.com/webservices/AddressBook"><abId>00000000-0000-0000-0000-000000000000</abId><contacts><Contact xmlns="http://www.msn.com/webservices/AddressBook"><contactInfo><passportName>%s</passportName><isMessengerUser>true</isMessengerUser></contactInfo></Contact></contacts><options><EnableAllowListManagement>true</EnableAllowListManagement></options></ABContactAdd></soap:Body></soap:Envelope>'''

contactRemove = '''<?xml version="1.0" encoding="utf-8"?><soap:Envelope xmlns:soap="http://schemas.xmlsoap.org/soap/envelope/" xmlns:xsi="http://www.w3.org/2001/XMLSchema-instance" xmlns:xsd="http://www.w3.org/2001/XMLSchema" xmlns:soapenc="http://schemas.xmlsoap.org/soap/encoding/">
<soap:Header><ABApplicationHeader xmlns="http://www.msn.com/webservices/AddressBook"><ApplicationId>CFE80F9D-180F-4399-82AB-413F33A1FA11</ApplicationId><IsMigration>false</IsMigration><PartnerScenario>Timer</PartnerScenario></ABApplicationHeader>
<ABAuthHeader xmlns="http://www.msn.com/webservices/AddressBook"><ManagedGroupRequest>false</ManagedGroupRequest><TicketToken>&tickettoken;</TicketToken></ABAuthHeader></soap:Header>
<soap:Body><ABContactDelete xmlns="http://www.msn.com/webservices/AddressBook"><abId>00000000-0000-0000-0000-000000000000</abId><contacts><Contact><contactId>%s</contactId></Contact></contacts></ABContactDelete></soap:Body></soap:Envelope>'''

# the first %s is Allow or Block, the second is the passport mail
# POST /abservice/SharingService.asmx HTTP/1.1
# SOAPAction: http://www.msn.com/webservices/AddressBook/DeleteMember
# Host: omega.contacts.msn.com
deleteMember='''<?xml version="1.0" encoding="utf-8"?><soap:Envelope xmlns:soap="http://schemas.xmlsoap.org/soap/envelope/" xmlns:xsi="http://www.w3.org/2001/XMLSchema-instance" xmlns:xsd="http://www.w3.org/2001/XMLSchema" xmlns:soapenc="http://schemas.xmlsoap.org/soap/encoding/">
<soap:Header><ABApplicationHeader xmlns="http://www.msn.com/webservices/AddressBook"><ApplicationId>CFE80F9D-180F-4399-82AB-413F33A1FA11</ApplicationId><IsMigration>false</IsMigration><PartnerScenario></PartnerScenario></ABApplicationHeader>
<ABAuthHeader xmlns="http://www.msn.com/webservices/AddressBook"><ManagedGroupRequest>false</ManagedGroupRequest><TicketToken>&tickettoken;</TicketToken></ABAuthHeader></soap:Header>
<soap:Body><DeleteMember xmlns="http://www.msn.com/webservices/AddressBook"><serviceHandle><Id>0</Id><Type>Messenger</Type><ForeignId></ForeignId></serviceHandle><memberships><Membership><MemberRole>%s</MemberRole><Members><Member xsi:type="PassportMember" xmlns:xsi="http://www.w3.org/2001/XMLSchema-instance"><Type>Passport</Type><State>Accepted</State><PassportName>%s</PassportName></Member></Members></Membership></memberships></DeleteMember></soap:Body></soap:Envelope>'''

# %s is the group name
# POST /abservice/abservice.asmx HTTP/1.1
# SOAPAction: http://www.msn.com/webservices/AddressBook/ABGroupAdd
# Host: by6.omega.contacts.msn.com

addGroup='''<?xml version="1.0" encoding="utf-8"?><soap:Envelope xmlns:soap="http://schemas.xmlsoap.org/soap/envelope/" xmlns:xsi="http://www.w3.org/2001/XMLSchema-instance" xmlns:xsd="http://www.w3.org/2001/XMLSchema" xmlns:soapenc="http://schemas.xmlsoap.org/soap/encoding/">
<soap:Header><ABApplicationHeader xmlns="http://www.msn.com/webservices/AddressBook"><ApplicationId>CFE80F9D-180F-4399-82AB-413F33A1FA11</ApplicationId><IsMigration>false</IsMigration><PartnerScenario>Timer</PartnerScenario></ABApplicationHeader>
<ABAuthHeader xmlns="http://www.msn.com/webservices/AddressBook"><ManagedGroupRequest>false</ManagedGroupRequest><TicketToken>&tickettoken;</TicketToken></ABAuthHeader></soap:Header>
<soap:Body><ABGroupAdd xmlns="http://www.msn.com/webservices/AddressBook"><abId>00000000-0000-0000-0000-000000000000</abId><groupAddOptions><fRenameOnMsgrConflict>false</fRenameOnMsgrConflict></groupAddOptions><groupInfo><GroupInfo><name>%s</name><groupType>C8529CE2-6EAD-434d-881F-341E17DB3FF8</groupType><fMessenger>false</fMessenger><annotations><Annotation><Name>MSN.IM.Display</Name><Value>1</Value></Annotation></annotations></GroupInfo></groupInfo></ABGroupAdd></soap:Body></soap:Envelope>'''


# the %s is the gid
# POST /abservice/abservice.asmx HTTP/1.1
# SOAPAction: http://www.msn.com/webservices/AddressBook/ABGroupDelete
# Host: by6.omega.contacts.msn.com

deleteGroup='''<?xml version="1.0" encoding="utf-8"?><soap:Envelope xmlns:soap="http://schemas.xmlsoap.org/soap/envelope/" xmlns:xsi="http://www.w3.org/2001/XMLSchema-instance" xmlns:xsd="http://www.w3.org/2001/XMLSchema" xmlns:soapenc="http://schemas.xmlsoap.org/soap/encoding/">
<soap:Header><ABApplicationHeader xmlns="http://www.msn.com/webservices/AddressBook"><ApplicationId>CFE80F9D-180F-4399-82AB-413F33A1FA11</ApplicationId><IsMigration>false</IsMigration><PartnerScenario>Timer</PartnerScenario></ABApplicationHeader>
<ABAuthHeader xmlns="http://www.msn.com/webservices/AddressBook"><ManagedGroupRequest>false</ManagedGroupRequest><TicketToken>&tickettoken;</TicketToken></ABAuthHeader></soap:Header>
<soap:Body><ABGroupDelete xmlns="http://www.msn.com/webservices/AddressBook"><abId>00000000-0000-0000-0000-000000000000</abId><groupFilter><groupIds><guid>%s</guid></groupIds></groupFilter></ABGroupDelete></soap:Body></soap:Envelope>'''

# gid, name
# POST abservice/abservice.asmx HTTP/1.1
# SOAPAction: http://www.msn.com/webservices/AddressBook/ABGroupUpdate
# Host: omega.contacts.msn.com/

renameGroup='''<?xml version="1.0" encoding="utf-8"?><soap:Envelope xmlns:soap="http://schemas.xmlsoap.org/soap/envelope/" xmlns:xsi="http://www.w3.org/2001/XMLSchema-instance" xmlns:xsd="http://www.w3.org/2001/XMLSchema" xmlns:soapenc="http://schemas.xmlsoap.org/soap/encoding/">
<soap:Header><ABApplicationHeader xmlns="http://www.msn.com/webservices/AddressBook"><ApplicationId>CFE80F9D-180F-4399-82AB-413F33A1FA11</ApplicationId><IsMigration>false</IsMigration><PartnerScenario>Timer</PartnerScenario></ABApplicationHeader>
<ABAuthHeader xmlns="http://www.msn.com/webservices/AddressBook"><ManagedGroupRequest>false</ManagedGroupRequest><TicketToken>&tickettoken;</TicketToken></ABAuthHeader></soap:Header>
<soap:Body><ABGroupUpdate xmlns="http://www.msn.com/webservices/AddressBook"><abId>00000000-0000-0000-0000-000000000000</abId><groups><Group><groupId>%s</groupId><groupInfo><name>%s</name></groupInfo><propertiesChanged>GroupName </propertiesChanged></Group></groups></ABGroupUpdate></soap:Body></soap:Envelope>'''

# MSN OIM module

# memberName,friendlyName,ver,buildVer,to,passport,appid,lockKey,seqNum,runId,content,
send_message = '''<?xml version="1.0" encoding="utf-8"?><soap:Envelope xmlns:xsi="http://www.w3.org/2001/XMLSchema-instance" xmlns:xsd="http://www.w3.org/2001/XMLSchema" xmlns:soap="http://schemas.xmlsoap.org/soap/envelope/"> <soap:Header><From memberName="$memberName" friendlyName="$friendlyName" xml:lang="en-US" proxy="MSNMSGR" xmlns="http://messenger.msn.com/ws/2004/09/oim/" msnpVer="$ver" buildVer="$buildVer"/><To memberName="$to" xmlns="http://messenger.msn.com/ws/2004/09/oim/"/><Ticket passport="$passport" appid="$appid" lockkey="$lockKey" xmlns="http://messenger.msn.com/ws/2004/09/oim/"/><Sequence xmlns="http://schemas.xmlsoap.org/ws/2003/03/rm"><Identifier xmlns="http://schemas.xmlsoap.org/ws/2002/07/utility">http://messenger.msn.com</Identifier><MessageNumber>$seqNum</MessageNumber></Sequence></soap:Header><soap:Body><MessageType xmlns="http://messenger.msn.com/ws/2004/09/oim/">text</MessageType><Content xmlns="http://messenger.msn.com/ws/2004/09/oim/">MIME-Version: 1.0\r\nContent-Type: text/plain; charset=UTF-8\r\nContent-Transfer-Encoding: base64\r\nX-OIM-Message-Type: OfflineMessage\r\nX-OIM-Run-Id: {$runId}\r\nX-OIM-Sequence-Num: $seqNum\r\n\r\n$content</Content></soap:Body></soap:Envelope>'''

#$t,$p,$mid
#retreive_message = '''<?xml version="1.0" encoding="utf-8"?><soap:Envelope xmlns:xsi="http://www.w3.org/2001/XMLSchema-instance" xmlns:xsd="http://www.w3.org/2001/XMLSchema" xmlns:soap="http://schemas.xmlsoap.org/soap/envelope/"><soap:Header><PassportCookie xmlns="http://www.hotmail.msn.com/ws/2004/09/oim/rsi"><t>$t</t><p>$p</p></PassportCookie></soap:Header><soap:Body><GetMessage xmlns="http://www.hotmail.msn.com/ws/2004/09/oim/rsi"><messageId>$mid</messageId><alsoMarkAsRead>false</alsoMarkAsRead></GetMessage></soap:Body></soap:Envelope>'''

retreive_message = '''<?xml version="1.0" encoding="utf-8"?> <soap:Envelope xmlns:xsi="http://www.w3.org/2001/XMLSchema-instance" xmlns:xsd="http://www.w3.org/2001/XMLSchema" xmlns:soap="http://schemas.xmlsoap.org/soap/envelope/">
<soap:Header>
<PassportCookie xmlns="http://www.hotmail.msn.com/ws/2004/09/oim/rsi"> <t>$t</t><p>$p</p> </PassportCookie>
</soap:Header>
<soap:Body>
<GetMessage xmlns="http://www.hotmail.msn.com/ws/2004/09/oim/rsi"> <messageId>$mid</messageId> <alsoMarkAsRead>false</alsoMarkAsRead> </GetMessage>
</soap:Body>
</soap:Envelope>'''

#$t,$p,$mid
delete_message = '''<?xml version="1.0" encoding="utf-8"?><soap:Envelope xmlns:xsi="http://www.w3.org/2001/XMLSchema-instance" xmlns:xsd="http://www.w3.org/2001/XMLSchema" xmlns:soap="http://schemas.xmlsoap.org/soap/envelope/"><soap:Header><PassportCookie xmlns="http://www.hotmail.msn.com/ws/2004/09/oim/rsi"><t>$t</t><p>$p</p></PassportCookie></soap:Header><soap:Body><DeleteMessages xmlns="http://www.hotmail.msn.com/ws/2004/09/oim/rsi"><messageIds><messageId>$mid</messageId></messageIds></DeleteMessages></soap:Body></soap:Envelope>'''

#POST /contactcard/contactcardservice.asmx HTTP/1.1
#Accept: */*
#SOAPAction: "http://www.msn.com/webservices/spaces/v1/GetXmlFeed"
#Content-Type: text/xml; charset=utf-8
#Content-Length: 2117
#User-Agent: Mozilla/4.0 (compatible; MSIE 6.0; Windows NT 5.1; SV1; .NET CLR 2.0.50727; Windows Live Messenger 8.1.0178)
#Host: cid-580B3F2402D4CDA4.cc.services.spaces.live.com
#Connection: Keep-Alive
#Cache-Control: no-cache
#Cookie: sc_stgclstbl_107=NzcwNTc1NjNjNDQyN2Q5NTE6d092QXNtdnJpUEJSeUxMNDNYTGRQQUViYzg5ZFFQUjJZRDdZWExVQm9XSmIvRlVkVGdURzJGRkI4dXM1QVFiVWdmMXBxTVBPREpIWFJEeXNlbTd5YWo0a3B4dEFqS0J3WERxcjZnWG8vZ3JCSkpqTms4cFN5VVJFNlk3d1RCU1hodnd1eGtmNDFPUWtVT01mYVg2NnJjWmd5NHBKK0hURlJiaUFnNTBBYjFBVm52T3hTeldRUVdJRkRxOEp4N1RDQThNeGN5T080VVJialFzTXVXdEdqYUxyN1B1UjRtTGZveDRRbDBHMXdlektkL0xuYzRQTytBPT0=; sc_identity_107=NGIyNzk5NWRlM2JkYTllODE6alJIOThQVU81Q0ZKOUlaMmkzekh0RjBLeUdkLzVJMnk0OExKeXBkdFBJVGpHNFZHUFR4aHZwemVrRkhrVGFlVkFUaURjRFZJQzErK0VKdlY4Q29qV2tuQ0kwSTFFME1mQnNHMVlPaUhDZ0k9; MUID=3A2C3E4B415C4C838835C3E5C8F46A38; ANON=A=307459359A8E113A91ADF680FFFFFFFF&E=5b8&W=6; NAP=V=1.5&E=55e&C=-8KnBX0ub9dkbKx1pzYK5iyQ3m0FIWFPCTZ-V_Pt7tS8Nan1ZV2Dxg&W=6

#t,p,cid,storageAuthCache,market
space='''<?xml version="1.0" ?>
<soap:Envelope xmlns:soap="http://schemas.xmlsoap.org/soap/envelope/" xmlns:xsd="http://www.w3.org/2001/XMLSchema" xmlns:xsi="http://www.w3.org/2001/XMLSchema-instance">
	<soap:Header>
		<AuthTokenHeader xmlns="http://www.msn.com/webservices/spaces/v1/">
			<Token>
				t=%s&amp;p=%s
			</Token>
		</AuthTokenHeader>
	</soap:Header>
	<soap:Body>
		<GetXmlFeed xmlns="http://www.msn.com/webservices/spaces/v1/">
			<refreshInformation>
				<cid xmlns="http://www.msn.com/webservices/spaces/v1/">
					%s
				</cid>
				<storageAuthCache>
					%s
				</storageAuthCache>
				<market xmlns="http://www.msn.com/webservices/spaces/v1/">
					%s
				</market>
				<brand/>
				<maxElementCount xmlns="http://www.msn.com/webservices/spaces/v1/">
					2
				</maxElementCount>
				<maxCharacterCount xmlns="http://www.msn.com/webservices/spaces/v1/">
					200
				</maxCharacterCount>
				<maxImageCount xmlns="http://www.msn.com/webservices/spaces/v1/">
					6
				</maxImageCount>
				<applicationId>
					Messenger Client 8.0
				</applicationId>
				<updateAccessedTime>
					true
				</updateAccessedTime>
				<spaceLastViewed>
					1753-01-01T00:00:00.0000000-00:00
				</spaceLastViewed>
				<profileLastViewed>
					1753-01-01T00:00:00.0000000-00:00
				</profileLastViewed>
				<contactProfileLastViewed>
					1753-01-01T00:00:00.0000000-00:00
				</contactProfileLastViewed>
				<isActiveContact>
					false
				</isActiveContact>
			</refreshInformation>
		</GetXmlFeed>
	</soap:Body>
</soap:Envelope>'''

#url "http://storage.msn.com/storageservice/schematizedstore.asmx"
#action "http://www.msn.com/webservices/storage/w10/GetItemVersion"

#cid
getProfile = '''<?xml version="1.0" encoding="utf-8"?><soap:Envelope xmlns:soap="http://schemas.xmlsoap.org/soap/envelope/" xmlns:xsi="http://www.w3.org/2001/XMLSchema-instance" xmlns:xsd="http://www.w3.org/2001/XMLSchema" xmlns:soapenc="http://schemas.xmlsoap.org/soap/encoding/"><soap:Header><StorageApplicationHeader xmlns="http://www.msn.com/webservices/storage/w10"><ApplicationID>Messenger Client 8.5</ApplicationID><Scenario>RoamingSeed</Scenario></StorageApplicationHeader><StorageUserHeader xmlns="http://www.msn.com/webservices/storage/w10"><Puid>0</Puid><TicketToken>&tickettoken;</TicketToken></StorageUserHeader></soap:Header><soap:Body><GetProfile xmlns="http://www.msn.com/webservices/storage/w10"><profileHandle><Alias><Name>%s</Name><NameSpace>MyCidStuff</NameSpace></Alias><RelationshipName>MyProfile</RelationshipName></profileHandle><profileAttributes><ResourceID>true</ResourceID><DateModified>true</DateModified><ExpressionProfileAttributes><ResourceID>true</ResourceID><DateModified>true</DateModified><DisplayName>true</DisplayName><DisplayNameLastModified>true</DisplayNameLastModified><PersonalStatus>true</PersonalStatus><PersonalStatusLastModified>true</PersonalStatusLastModified><StaticUserTilePublicURL>true</StaticUserTilePublicURL><Photo>true</Photo><Flags>true</Flags></ExpressionProfileAttributes></profileAttributes></GetProfile></soap:Body></soap:Envelope>'''

#affinityCache,rid,nick,pm
updateProfile = '''<?xml version="1.0" encoding="utf-8"?><soap:Envelope xmlns:soap="http://schemas.xmlsoap.org/soap/envelope/" xmlns:xsi="http://www.w3.org/2001/XMLSchema-instance" xmlns:xsd="http://www.w3.org/2001/XMLSchema" xmlns:soapenc="http://schemas.xmlsoap.org/soap/encoding/"><soap:Header><AffinityCacheHeader xmlns="http://www.msn.com/webservices/storage/w10"><CacheKey>%s</CacheKey></AffinityCacheHeader><StorageApplicationHeader xmlns="http://www.msn.com/webservices/storage/w10"><ApplicationID>Messenger Client 8.5</ApplicationID><Scenario>RoamingIdentityChanged</Scenario></StorageApplicationHeader><StorageUserHeader xmlns="http://www.msn.com/webservices/storage/w10"><Puid>0</Puid><TicketToken>&tickettoken;</TicketToken></StorageUserHeader></soap:Header><soap:Body><UpdateProfile xmlns="http://www.msn.com/webservices/storage/w10"><profile><ResourceID>%s</ResourceID><ExpressionProfile><FreeText>Update</FreeText><DisplayName>%s</DisplayName><PersonalStatus>%s</PersonalStatus><Flags>0</Flags></ExpressionProfile></profile></UpdateProfile></soap:Body></soap:Envelope>'''

# - nothing
createProfile = '''<?xml version="1.0" encoding="utf-8"?><soap:Envelope xmlns:soap="http://schemas.xmlsoap.org/soap/envelope/" xmlns:xsi="http://www.w3.org/2001/XMLSchema-instance" xmlns:xsd="http://www.w3.org/2001/XMLSchema" xmlns:soapenc="http://schemas.xmlsoap.org/soap/encoding/"><soap:Header><StorageApplicationHeader xmlns="http://www.msn.com/webservices/storage/w10"><ApplicationID>Messenger Client 8.5</ApplicationID><Scenario>RoamingSeed</Scenario></StorageApplicationHeader><StorageUserHeader xmlns="http://www.msn.com/webservices/storage/w10"><Puid>0</Puid><TicketToken>&tickettoken;</TicketToken></StorageUserHeader></soap:Header><soap:Body><CreateProfile xmlns="http://www.msn.com/webservices/storage/w10"><profile><ExpressionProfile><PersonalStatus/><RoleDefinitionName>ExpressionProfileDefault</RoleDefinitionName></ExpressionProfile></profile></CreateProfile></soap:Body></soap:Envelope>'''

#affinitycache, cid, name, mimetype, data
updateDp = '''<?xml version="1.0" encoding="utf-8"?><soap:Envelope xmlns:soap="http://schemas.xmlsoap.org/soap/envelope/" xmlns:xsi="http://www.w3.org/2001/XMLSchema-instance" xmlns:xsd="http://www.w3.org/2001/XMLSchema" xmlns:soapenc="http://schemas.xmlsoap.org/soap/encoding/"><soap:Header><AffinityCacheHeader xmlns="http://www.msn.com/webservices/storage/w10"><CacheKey>%s</CacheKey></AffinityCacheHeader><StorageApplicationHeader xmlns="http://www.msn.com/webservices/storage/w10"><ApplicationID>Messenger Client 8.5</ApplicationID><Scenario>RoamingIdentityChanged</Scenario></StorageApplicationHeader><StorageUserHeader xmlns="http://www.msn.com/webservices/storage/w10"><Puid>0</Puid><TicketToken>&tickettoken;</TicketToken></StorageUserHeader></soap:Header><soap:Body><CreateDocument xmlns="http://www.msn.com/webservices/storage/w10"><parentHandle><RelationshipName>/UserTiles</RelationshipName><Alias><Name>%s</Name><NameSpace>MyCidStuff</NameSpace></Alias></parentHandle><document xsi:type="Photo"><Name>%s</Name><DocumentStreams><DocumentStream xsi:type="PhotoStream"><DocumentStreamType>UserTileStatic</DocumentStreamType><MimeType>%s</MimeType><Data>%s</Data><DataSize>0</DataSize></DocumentStream></DocumentStreams></document><relationshipName>Messenger User Tile</relationshipName></CreateDocument></soap:Body></soap:Envelope>'''

#affinitycache,rid,did
createRelationships = '''<?xml version="1.0" encoding="utf-8"?><soap:Envelope xmlns:soap="http://schemas.xmlsoap.org/soap/envelope/" xmlns:xsi="http://www.w3.org/2001/XMLSchema-instance" xmlns:xsd="http://www.w3.org/2001/XMLSchema" xmlns:soapenc="http://schemas.xmlsoap.org/soap/encoding/"><soap:Header><AffinityCacheHeader xmlns="http://www.msn.com/webservices/storage/w10"><CacheKey>%s</CacheKey></AffinityCacheHeader><StorageApplicationHeader xmlns="http://www.msn.com/webservices/storage/w10"><ApplicationID>Messenger Client 8.5</ApplicationID><Scenario>RoamingIdentityChanged</Scenario></StorageApplicationHeader><StorageUserHeader xmlns="http://www.msn.com/webservices/storage/w10"><Puid>0</Puid><TicketToken>&tickettoken;</TicketToken></StorageUserHeader></soap:Header><soap:Body><CreateRelationships xmlns="http://www.msn.com/webservices/storage/w10"><relationships><Relationship><SourceID>%s
</SourceID><SourceType>SubProfile</SourceType><TargetID>%s</TargetID><TargetType>Photo</TargetType><RelationshipName>ProfilePhoto</RelationshipName></Relationship></relationships></CreateRelationships></soap:Body></soap:Envelope>'''

#affinity cache,cid
findDocument = '''<?xml version="1.0" encoding="utf-8"?><soap:Envelope xmlns:soap="http://schemas.xmlsoap.org/soap/envelope/" xmlns:xsi="http://www.w3.org/2001/XMLSchema-instance" xmlns:xsd="http://www.w3.org/2001/XMLSchema" xmlns:soapenc="http://schemas.xmlsoap.org/soap/encoding/"><soap:Header><AffinityCacheHeader xmlns="http://www.msn.com/webservices/storage/w10"><CacheKey>%s</CacheKey></AffinityCacheHeader><StorageApplicationHeader xmlns="http://www.msn.com/webservices/storage/w10"><ApplicationID>Messenger Client 8.5</ApplicationID><Scenario>RoamingIdentityChanged</Scenario></StorageApplicationHeader><StorageUserHeader xmlns="http://www.msn.com/webservices/storage/w10"><Puid>0</Puid><TicketToken>&tickettoken;</TicketToken></StorageUserHeader></soap:Header><soap:Body><FindDocuments xmlns="http://www.msn.com/webservices/storage/w10"><objectHandle><RelationshipName>/UserTiles</RelationshipName><Alias><Name>%s</Name><NameSpace>MyCidStuff</NameSpace></Alias></objectHandle><documentAttributes><ResourceID>true</ResourceID><Name>true</Name></documentAttributes><documentFilter><FilterAttributes>None</FilterAttributes></documentFilter><documentSort><SortBy>DateModified</SortBy></documentSort><findContext><FindMethod>Default</FindMethod><ChunkSize>25</ChunkSize></findContext></FindDocuments></soap:Body></soap:Envelope>'''


#affinitycache, cid, dpid
deleteRelationship1 = '''<?xml version="1.0" encoding="utf-8"?><soap:Envelope xmlns:soap="http://schemas.xmlsoap.org/soap/envelope/" xmlns:xsi="http://www.w3.org/2001/XMLSchema-instance" xmlns:xsd="http://www.w3.org/2001/XMLSchema" xmlns:soapenc="http://schemas.xmlsoap.org/soap/encoding/"><soap:Header><AffinityCacheHeader xmlns="http://www.msn.com/webservices/storage/w10"><CacheKey>%s</CacheKey></AffinityCacheHeader><StorageApplicationHeader xmlns="http://www.msn.com/webservices/storage/w10"><ApplicationID>Messenger Client 8.5</ApplicationID><Scenario>RoamingIdentityChanged</Scenario></StorageApplicationHeader><StorageUserHeader xmlns="http://www.msn.com/webservices/storage/w10"><Puid>0</Puid><TicketToken>&tickettoken;</TicketToken></StorageUserHeader></soap:Header><soap:Body><DeleteRelationships xmlns="http://www.msn.com/webservices/storage/w10"><sourceHandle><RelationshipName>/UserTiles</RelationshipName><Alias><Name>%s</Name><NameSpace>MyCidStuff</NameSpace></Alias></sourceHandle><targetHandles><ObjectHandle><ResourceID>%s</ResourceID></ObjectHandle></targetHandles></DeleteRelationships></soap:Body></soap:Envelope>'''

#affinitycache, rid, dpid
deleteRelationship2 = '''<?xml version="1.0" encoding="utf-8"?><soap:Envelope xmlns:soap="http://schemas.xmlsoap.org/soap/envelope/" xmlns:xsi="http://www.w3.org/2001/XMLSchema-instance" xmlns:xsd="http://www.w3.org/2001/XMLSchema" xmlns:soapenc="http://schemas.xmlsoap.org/soap/encoding/"><soap:Header><AffinityCacheHeader xmlns="http://www.msn.com/webservices/storage/w10"><CacheKey>%s</CacheKey></AffinityCacheHeader><StorageApplicationHeader xmlns="http://www.msn.com/webservices/storage/w10"><ApplicationID>Messenger Client 8.5</ApplicationID><Scenario>RoamingIdentityChanged</Scenario></StorageApplicationHeader><StorageUserHeader xmlns="http://www.msn.com/webservices/storage/w10"><Puid>0</Puid><TicketToken>&tickettoken;</TicketToken></StorageUserHeader></soap:Header><soap:Body><DeleteRelationships xmlns="http://www.msn.com/webservices/storage/w10"><sourceHandle><ResourceID>%s</ResourceID></sourceHandle><targetHandles><ObjectHandle><ResourceID>%s</ResourceID></ObjectHandle></targetHandles></DeleteRelationships></soap:Body></soap:Envelope>'''

#t, p
getMailData = '''<?xml version="1.0" encoding="utf-8"?><soap:Envelope xmlns:xsi="http://www.w3.org/2001/XMLSchema-instance" xmlns:xsd="http://www.w3.org/2001/XMLSchema" xmlns:soap="http://schemas.xmlsoap.org/soap/envelope/"><soap:Header><PassportCookie xmlns="http://www.hotmail.msn.com/ws/2004/09/oim/rsi"><t>%s</t><p>%s</p></PassportCookie></soap:Header><soap:Body><GetMetadata xmlns="http://www.hotmail.msn.com/ws/2004/09/oim/rsi"/></soap:Body></soap:Envelope>'''

