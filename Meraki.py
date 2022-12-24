#Import packages
import meraki
from netmiko import ConnectHandler
import csv
import Keys
import subprocess
import time

#Connect to dashboard using API key
dashboard = meraki.DashboardAPI(Keys.dashboard_Key)


#Function to configure switch port
def conf_sw(hostname, sw_port, wall_port, ap_name, vlan_num, native_vlan):


    cisco_sw = {
        'device_type': 'cisco_ios',
        'host':   hostname,
        'username': Keys.sw_username,
        'password': Keys.sw_passwd,
        'port' : 22,
        'secret': Keys.enable_pwd
    }

    #Connect to switch and enter enable mode
    net_connect = ConnectHandler(**cisco_sw)
    net_connect.enable()

    #Commands to configure on switch
    config_commands = [ 'default interface '+ sw_port,
                        'int '+ sw_port,
                        'description '+ wall_port + ' ' + ap_name,
                        'switchport trunk native vlan '+ native_vlan,
                        'switchport trunk allowed vlan + native_vlan +',' + vlan_num,
                        'switchport mode trunk',
                        'shut',
                        'no shut']
    net_connect.send_config_set(config_commands)
    print("Switch configured for " + ap_name )

# Read CSV file and configure dashboard and switch
with open('AP_list.csv') as readCsv:
    reader = csv.reader(readCsv, delimiter=',')
    #Ignores headers and blank
    next(reader, None)

    #Loop to go through CSV file
    for row in reader:
        try:
            #Add Meraki device to dashboard
            dashboard.organizations.claimIntoOrganizationInventory(Keys.organization_id,serials=[row[1]])
        except:
            print(f"The Serial No {row[1]} is already claimed")
        try:
            #Claim Meraki to Network
            dashboard.networks.claimNetworkDevices(Keys.nw_id, serials=[row[1]])
        except:
            print(f"The Serial No {row[1]} is already in network")
        finally:
            #Configure Meraki devices
            dashboard.devices.updateDevice(row[1], name=row[0], address=row[2], tags=[row[9]] )
            #Configure Meraki management interface
            dashboard.devices.updateDeviceManagementInterface(row[1], wan1={'usingStaticIp': row[3], 'staticIp': row[4], 'staticSubnetMask': row[5], 'staticGatewayIp': row [6], 'staticDns': [row[7],row[8]]})
            #Calls Switch configuration function
            conf_sw(row[10],row[11], row[12], row[0], row[13], row[14])
            print("Dashboard configured for " + row[0])
            #Configure Windows Radius servers
	    PwShell_cmd = 'Invoke-Command -ComputerName ' + row[15] + ' -ScriptBlock {New-NpsRadiusClient -Address ' + row[4] + ' -Name BM-' + row[0] + ' -SharedSecret ' + Keys.radius_Key + ' }'
            subprocess.run(['Powershell',PwShell_cmd])
            print("Radius configured for " + row[0])
            #Meraki rate limits 5 requests per sec
	    time.sleep(1)
