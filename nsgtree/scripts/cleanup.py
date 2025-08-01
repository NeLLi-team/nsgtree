import sys
import tarfile
import os.path
import shutil


def make_tarfile(tarout, resultsdir):
    with tarfile.open(tarout, "w:gz") as tar:
        tar.add(resultsdir, arcname=os.path.basename(resultsdir))
        try:
            shutil.rmtree(resultsdir)
        except OSError as e:
            print("Error: %s : %s" % (resultsdir, e.strerror))


def main(args=None):
    if args is None:
        args = sys.argv[1:]

    resultsdir = args[0]
    tarout = args[1]

    make_tarfile(tarout, resultsdir)


if __name__ == "__main__":
    main()
