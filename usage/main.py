from sg800m import Reader
inputPath = "Z:/" # /cluster/work/ciank/
outputPath = "./output"
if __name__ == "__main__":
    reader = Reader(inputPath, outputPath, releaseNumber=1)