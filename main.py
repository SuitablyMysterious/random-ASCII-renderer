import png, json

# Load config file

configFilePath = "config.json"
with open(configFilePath) as f:
    configFile = json.load(f)

# Define the PNG reader, and load the file

pngReader = png.Reader(configFile["imagePath"])
width, height, pixels, metadata = pngReader.read()

# Turn imported pixels into a list

pixelList = list(pixels)
