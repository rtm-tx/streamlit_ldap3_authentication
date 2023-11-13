import streamlit as st
import extra_streamlit_components as stx
from ldap3 import Server, Connection, ALL, NTLM, SUBTREE
import datetime

LDAP_SERVER = 'kstg.corp'
SERVICE_ACCOUNT_USERNAME = 'KSTG\SUS0135-AP'
SERVICE_ACCOUNT_PASSWORD = '$Tr3Amc0N3Ct!'  # Replace with the actual password
GROUP_DN = ['CN=StreamConnect Neo support,OU=Distribution Lists,OU=ELS,OU=AMER,DC=KSTG,DC=corp',
            'CN=Usage Reports,OU=Distribution Lists,OU=ELS,OU=AMER,DC=KSTG,DC=corp']  # Update this as per your LDAP structure
BASE_DN = 'DC=KSTG,DC=corp'  # Base DN for your LDAP server

LDAP_SERVER = ''
SERVICE_ACCOUNT_USERNAME = ''
SERVICE_ACCOUNT_PASSWORD = ''  # Replace with the actual password
GROUP_DN = ['fullDNofGroup1',
            'fullDNofGroup1']  # Update this as per your LDAP structure
BASE_DN = 'BaseDomainDN'  # Base DN for your LDAP server

def get_manager():
    return stx.CookieManager()

cookie_manager = get_manager()

def find_user_dn(server, service_account_username, service_account_password, username):
    with Connection(server, user=service_account_username, password=service_account_password, authentication=NTLM) as conn:
        conn.search(search_base=BASE_DN,
                    search_filter=f'(sAMAccountName={username})',
                    search_scope=SUBTREE,
                    attributes=['*'])
        return str(conn.entries[0].entry_dn) if len(conn.entries) > 0 else None

def is_user_in_group(server, user_dn, username, password, group_dns):
    with Connection(server, user=username, password=password, authentication=NTLM) as conn:
        for group_dn in group_dns: # Check if the user is a member of any of the groups in GROUP_DN
            conn.search(search_base=user_dn,
                        search_filter=f'(memberOf={group_dn})',
                        search_scope=SUBTREE,
                        attributes=['cn'])
            if len(conn.entries) > 0: # If the user is a member of the group, return True
                return True
        return False # If the user is not a member of any of the groups, return False

def main():
    
    L1, L2, L3 = st.columns([2,1,2])
    with L2:
        st.title("OR1 Utilization Analytics Demo")
        
        auth_cookie = cookie_manager.get('auth')

        if auth_cookie == 'true':
            st.write("Welcome!")
            return True
        else:
            
            username = st.text_input("Username")
            password = st.text_input("Password", type="password")

            if st.button("Log in"):
                server = Server(LDAP_SERVER)

                # Process the username
                if '\\' in username:
                    domain, username = username.split('\\')
                else:
                    domain = LDAP_SERVER.split('.')[0]

                # Try to bind with the provided credentials
                user_conn = None
                try:
                    user_conn = Connection(server, user=f'{domain}\\{username}', password=password, authentication=NTLM, auto_bind=True)
                except:
                    st.write("Could not log in.")

                if user_conn and user_conn.bound:
                    # Find the user's DN based on the username
                    user_dn = find_user_dn(server, SERVICE_ACCOUNT_USERNAME, SERVICE_ACCOUNT_PASSWORD, username)
                    
                    # Check if the user belongs to the required group
                    if user_dn and is_user_in_group(server, user_dn, SERVICE_ACCOUNT_USERNAME, SERVICE_ACCOUNT_PASSWORD, GROUP_DN):
                        cookie_manager.set('auth', 'true', expires_at=datetime.datetime.now() + datetime.timedelta(minutes=30))
                        st.write("Welcome!")
                        return True
                    else:
                        st.write("You're not a member of the required group.")
                        return False
                else:
                    st.write("Invalid username or password.")
                    return False
    return False

if __name__ == "__main__":
    main()
