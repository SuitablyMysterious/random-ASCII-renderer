import png, json

# Load config file

def readConfig(configPath):
    with open(configPath, "r") as cfg:
        return json.load(cfg)

configFile = readConfig("config.json")
characterConfig = readConfig("characters/config.json")

# Define the PNG reader, and load the file

pngReader = png.Reader(configFile["imagePath"])
width, height, pixels, metadata = pngReader.read()

# Turn imported pixels into a list

pixelList = list(pixels)


