import argparse
import sys
import testscreen

def CommandLine():
    print("hi")
    parser = argparse.ArgumentParser(description = "Description for my parser")
    parser.add_argument("-H", "--Help", help = "Example: Help argument", required = False, default = "")
    parser.add_argument("-s", "--save", help = "Example: Save argument", required = False, default = "")
    parser.add_argument("-p", "--print", help = "Example: Print argument", required = False, default = "")
    parser.add_argument("-o", "--output", help = "Example: Output argument", required = False, default = "")
    parsed_args, unparsed_args = parser.parse_known_args()
    status = False
    print(parsed_args)    
    if parsed_args.Help:
        print("You have used '-H' or '--Help' with argument: {0}".format(argument.Help))
        status = True
    if parsed_args.save:
        print("You have used '-s' or '--save' with argument: {0}".format(argument.save))
        status = True
    if parsed_args.print:
        print("You have used '-p' or '--print' with argument: {0}".format(argument.print))
        status = True
    if parsed_args.output:
        print("You have used '-o' or '--output' with argument: {0}".format(argument.output))
        status = True
    if not status:
        print("Maybe you want to use -H or -s or -p or -p as arguments ?")
    
    return(parsed_args, unparsed_args)

if __name__ == '__main__':
    parsed_args, unparsed_args = CommandLine()
    qt_args = sys.argv[:1] + unparsed_args
    #JetTracking(qt_args)

