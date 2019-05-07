#!/usr/bin/python

import multiprocessing, os, time, sys, getopt
from multiprocessing import Manager

def usage():
    print sys.argv[0] + " ( -h, --help ) ( -d, --dnsonly ) ( -f, --free ) ( -u --used ) ( -p --pingonly ) ( -c --clean ) -s /24 subnet like 172.16.220"

def parse_args(args):
    if len(args) == 1:
        usage()
        sys.exit()
    try:
        opts, arg = getopt.getopt(args[1:], "hdfupcs:", [ "help", "dnsonly", "free", "used", "pingonly", "clean", "subnet=" ])
    except getopt.GetoptError as err:
        print str(err)
        usage()
        sys.exit(2)
    options = [ False, False, False, False, False, None ] 
    for o, a in opts:
        if o == "-h" or o == "--help":
            usage()
            sys.exit()
        elif o == None:
            print "No Options:"
            usage()
            sys.exit()
        elif o == "-d" or o == "--dnsonly":
            options[0] = True
        elif o == "-f" or o == "--free":
            options[1] =  True
        elif o == "-u" or o == "--used":
            options[2] = True
        elif o == "-p" or o == "--pingonly":
            options[3] = True
        elif o == "-c" or o == "--clean":
            options[4] = True
        elif o == "-s" or o == "--subnet":
            options[5] = a
        else:
            print "Error, unknown option " + o
            usage()
            sys.exit()
    # if all are False, they are all True for printing... nothing specified
    if not options[0] and not options[1] and not options[2] and not options[3]:
        for i in range(0,4):
            options[i] = True
    return options

def check_ip ( ip, ips ):
    ignore_ips = [ '172.16.21.200', '172.16.21.201', '172.16.21.202', '172.16.21.203', '172.16.21.204', 
            '172.16.12.215', '172.16.12.216', '172.16.12.217', '172.16.12.218', '172.16.12.219',
            '172.16.24.215', '172.16.24.216', '172.16.24.217', '172.16.24.218', '172.16.24.219',
            '172.16.20.102', '172.16.20.103', '172.16.20.152', '172.16.20.153', '172.16.20.154' ]
    ping_response = os.popen("ping -c 1 " + ip).read().split()[-3:]
    host_response = os.popen("host " + ip).read().split()[4]
    if ping_response[0] == 'loss,' and ip not in ignore_ips: 
        ips [ ip ] = host_response + ' ' + ' '.join(ping_response)
    elif ping_response != 'loss,' and ip not in ignore_ips:
        ips [ ip ] = host_response

def spawn_jobs ( subnet, ips ):
    jobs=[]
    for i in range(1,254):
        ip = subnet + "." + str(i)
        p = multiprocessing.Process(target=check_ip, args=(ip, ips ))
        jobs.append(p)
        p.start()

    wait = True
    while wait:
        wait = False
        for j in jobs:
            if j.is_alive() == True:
                wait = True
        time.sleep(0.5)

def sort_ips(ip_list):
    subnet = '.'.join(ip_list[0].split('.')[0:3])
    last_octets = []
    tmp_array = []
    for ip in ip_list:
        last_octets.append(ip.split('.')[3])
    last_octets.sort(key=int)
    for last_octet in last_octets:
        tmp_array.append( subnet  + "." + last_octet)
    return tmp_array


def print_output(options,ips):
    dnsonly = []
    free = []
    used = []
    pingonly = []
    # options [ dns, free, used, ping, clean, subnet ] -- reference
    for key in ips.keys():
        test = ips[key].split()
        if len(test) == 1 and test[0] == '3(NXDOMAIN)':
            pingonly.append(key)
        elif len(test) == 1:
            used.append(key)
        elif len(test) == 4 and test[0] == '3(NXDOMAIN)':
            free.append(key)
        elif len(test) == 4:
            dnsonly.append(key)
    dnsonly_sorted = sort_ips(dnsonly)
    free_sorted = sort_ips(free)
    used_sorted = sort_ips(used)
    pingonly_sorted = sort_ips(pingonly)
    if options[1]:
        print "Free IPs:"
        print "******************************"
        for ip in free_sorted:
            if options[4]:
                print ip
            else:
                print ip + " " + ips[ip]
        print
    if options[0]:
        print "DNS only IPs:"
        print "******************************"
        for ip in dnsonly_sorted:
            if options[4]:
                print ip
            else:
                print ip + " " + ips[ip]
        print
    if options[3]:
        print "Pingable only IPs:"
        print "******************************"
        for ip in pingonly_sorted:
            if options[4]:
                print ip
            else:
                print ip + " " + ips[ip]
        print
    if options[2]:
        print "Used IPs:"
        print "******************************"
        for ip in used_sorted:
            if options[4]:
                print ip
            else:
                print ip + " " + ips[ip]
        print

def main(args):
    # required to save output from commands with multiprocessing
    manager = Manager()
    ips = manager.dict()

    options = parse_args(args)
    spawn_jobs( options[-1], ips )
    print_output(options,ips)


if __name__ == '__main__':
    main(sys.argv)

