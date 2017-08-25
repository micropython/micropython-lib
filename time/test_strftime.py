import sys
import getopt
import time


def arg_check(argv):
    try:
        opts, args = getopt.getopt(argv[1:], 'hv', ['help', 'verbose'])
    except getopt.GetoptError:
        print(argv[0] + ' -h -v')
        sys.exit(2)
    for opt, arg in opts:
        if opt == '-h':
            print(argv[0] + ' <usage> -h <help> -v <verbose>')
            print(argv[0] + ' <usage> -h prints this help')
            print(argv[0] + ' <usage> -v prints detailed test results')
            sys.exit()
        elif opt in '-v':
            return True
        else:
            return False


def gen_time_result(gen_test_time_ip):
    return str(gen_test_time_ip[0]) +\
      (('0'+str(gen_test_time_ip[1])) if (len(str(gen_test_time_ip[1])) == 1) else str(gen_test_time_ip[1])) +\
      (('0'+str(gen_test_time_ip[2])) if (len(str(gen_test_time_ip[2])) == 1) else str(gen_test_time_ip[2])) +\
      (('0'+str(gen_test_time_ip[3])) if (len(str(gen_test_time_ip[3])) == 1) else str(gen_test_time_ip[3])) +\
      (('0'+str(gen_test_time_ip[4])) if (len(str(gen_test_time_ip[4])) == 1) else str(gen_test_time_ip[4])) +\
      (('0'+str(gen_test_time_ip[5])) if (len(str(gen_test_time_ip[5])) == 1) else str(gen_test_time_ip[5]))


if __name__ == '__main__':

    # Check the arguments passed to this program
    #
    verbose=arg_check(sys.argv)

    # The following array consists of several time elements that will be
    # input to the the strftime method. These tuples were generated using
    # localtime() and gmtime() in core python.
    #
    test_time_ip = ((2017, 1,  1,  23, 40, 39, 6, 222, 1),
                    (2010, 2,  28, 9,  59, 60, 1, 111, 0),
                    (2000, 3,  31, 1,  33, 0,  2, 44,  1),
                    (2020, 4,  30, 21, 22, 59, 3, 234, 0),
                    (1977, 5,  15, 23, 55, 1,  4, 123, 1),
                    (1940, 6,  11, 9,  21, 33, 5, 55,  0),
                    (1918, 7,  24, 6,  12, 44, 7, 71,  1),
                    (1800, 8,  17, 0,  59, 55, 3, 89,  0),
                    (2222, 9,  5,  1,  0,  4,  2, 255, 1),
                    (2017, 10, 10, 9,  1,  5,  6, 200, 0),
                    (2016, 11, 7,  18, 8,  16, 7, 100, 1),
                    (2001, 12, 2,  12, 19, 27, 1, 33,  0),
                    (time.localtime()),
                    (time.gmtime()))

    # The following array consists of results generated using strftime(localtime())
    # and strftime(gmtime()) in core python.
    #
    test_core_python_time_op = (('20170101234039'),  # pass 0
                                ('20100228095960'),  # pass 1
                                ('20000331013300'),  # pass 2
                                ('20200430212259'),  # pass 3
                                ('19770515235501'),  # pass 4
                                ('19400611092133'),  # pass 5
                                ('19180724061244'),  # pass 6
                                ('18000817005955'),  # pass 7
                                ('22220905010004'),  # pass 8
                                ('20171010090105'),  # pass 9
                                ('20161107180816'),  # pass 10
                                ('20011202121927'),  # pass 11
                                (gen_time_result(test_time_ip[len(test_time_ip)-2])),
                                (gen_time_result(test_time_ip[len(test_time_ip) - 1])))

    # test_core_python_time_op = (('20170101134039'),  # fail 0
    #                             ('20100228095960'),  # pass 1
    #                             ('20000331013300'),  # pass 2
    #                             ('20200430212259'),  # pass 3
    #                             ('19770512235501'),  # fail 4
    #                             ('19400611092133'),  # pass 5
    #                             ('19180724061244'),  # pass 6
    #                             ('18000817005955'),  # pass 7
    #                             ('22220907710004'),  # fail 8
    #                             ('20171010090105'),  # pass 9
    #                             ('20161107180816'),  # pass 10
    #                             ('20011202120027'))  # fail 11

    if verbose:
        for i in range(len(test_time_ip)):
            time_dot_strftime_op = time.strftime('%Y%m%d%H%M%S', test_time_ip[i])
            print('******************************************')
            print('Input Time to strftime: ', test_time_ip[i])
            print('Output Time of strftime: ', time_dot_strftime_op)
            print('Core Python Result of strftime: ', test_core_python_time_op[i])
            print('Test Status: ', ('PASS' if time_dot_strftime_op == test_core_python_time_op[i] else 'FAIL'))
    else:
        print()
        print({i:('PASS' if time.strftime('%Y%m%d%H%M%S', test_time_ip[i]) == test_core_python_time_op[i] else 'FAIL')
               for i in range(len(test_time_ip))})
        print()