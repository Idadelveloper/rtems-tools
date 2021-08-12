
import argparse
import os
import sys
import re

from rtemstoolkit import execute
from rtemstoolkit import git


def get_command():
    from rtemstoolkit import check

    for version in ['', '8', '9', '10', '11']:
        if check.check_exe(None, 'clang-format' + version):
            command = 'clang-format' + version
            return command
    print("Clang-format not found in your system")
    sys.exit(1)


def arguments():
    parser = argparse.ArgumentParser(description="Tool for code formatting and style checking \
        for RTEMS")
    parser.add_argument("-c", "--check", dest="check", help="Check for style differences and \
        report the number of issues if found", action="store_true")
    parser.add_argument("-r", "--reformat", dest="reformat", help="Reformat the file/directory \
        with any style differences found", action="store_true")
    parser.add_argument("-p", "--path", dest="path", help="The path to be checked for style issues \
        or reformatted")
    parser.add_argument("-i", "--ignore", dest="ignore", help="Ignore files to be checked or \
        reformatted", nargs='*')
    parser.add_argument("-v", "--verbose", dest="verbose", help="A more detailed outline of the \
        style issues", action='store_true')
    return [parser.parse_args(), parser.print_usage()]


def get_diff(path, ignore_file):
    diff = ""
    ex = execute.capture_execution()

    def clang_to_git_diff(clang_output, path):
        import os
        import tempfile

        fd, tmp_path = tempfile.mkstemp()
        try:
            with os.fdopen(fd, 'w') as tmp:
                
                tmp.write(clang_output)
                repo = git.repo(".")
            return repo.diff(['--no-index', path, tmp_path])
                
        finally:
            os.remove(tmp_path)

    if os.path.isfile(path) == True:
        cmd = get_command() + " --style=file " + path
        output_clang = ex.command(command=cmd, shell=True)
        output_clang = output_clang[2]
        diff = clang_to_git_diff(output_clang, path)
    else:
        onlyfiles = [f for f in os.listdir(path)]
        for file in onlyfiles:
            ig_match = False
            if ignore_file is not None:
                for f in ignore_file:
                    if file == f:
                        ig_match = True
                if ig_match == True:
                    continue
                
            file = os.path.join(path, file)

            if file.endswith('.c') or file.endswith('.h'):
                cmd = get_command() + " --style=file " + file
                output_clang = ex.command(command=cmd, shell=True)
                output_clang = output_clang[2]
                diff += clang_to_git_diff(output_clang, os.path.join(path, file))
    return diff


def color_text(string, col, style=1):
    return "\033[" + str(style) + ";" + str(col) + ";" + str(col) + "m" + string + "\033[0;0m"


def handle_errors(path, output, verbose=False,):
    if len(output) < 1:
        print("Everything is clean - No style issues")
    else:
        print(color_text("Checking for style differences...", 34, style=3))

        out = output.split('\n')
        files = []
        num_diff = 0
        for line in out:

            if line.startswith("---"):
                file = str(re.sub('^---\s[ab]', '', line))
                files.append(file)
            
            elif line.startswith('+'):
                num_diff += 1
                if verbose == True:
                    print(color_text(line, 34))
                    continue
            if verbose == True:
                print(line)
            
        print(color_text("\nFiles affected:", 33))

        for file in files:
            print(file)
        
        message = "\nStyleWarning: You have about a total of " + str(num_diff) + \
                " style issue(s) in the " + str(len(files)) + " file(s) listed above"
        print(color_text(message, 31))


def reformat(path, output):
    if len(output) > 0:
        onlyfiles = [f for f in os.listdir(path)]
        for file in onlyfiles:
            if file.endswith('.c') or file.endswith('.h'):
                cmd = get_command() + " -i -style=file " + os.path.join(path, file)
                ex = execute.capture_execution()
                ex.command(command=cmd, shell=True)
    else:
        print("Everything is clean. No style issues")
        return 0


def run(args = sys.argv):
    args = arguments()
    if args[0].path == None:
        print("A path is required")
        sys.exit(1)
    print(args[0].path)
    path = os.path.abspath(args[0].path)
    if os.path.exists(path) == False:
        print("Please enter a correct path!!")
        sys.exit(1)
    output = get_diff(path, args[0].ignore)
    if args[0].check == True:
        handle_errors(path, output, verbose=args[0].verbose)
    elif args[0].reformat == True:
        reformat(path, output)
    else:
        args[1]
        sys.exit(1)


if __name__ == "__main__":
    run()

