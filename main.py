import png, json
import os
from PIL import Image

# Load config file

def readConfig(configPath):
    with open(configPath, "r") as cfg:
        return json.load(cfg)

def findLightness(manifestMap, image):

    image = image.convert("L")
    pixels = image.getdata()
    return (sum(pixels) / len(pixels))



configFile = readConfig("config.json")
characterConfig = readConfig(configFile["characterConfigPath"])
characterLightnessMap = readConfig(configFile["characterLightnessPath"])
characterManifestMap = readConfig(configFile["characterManifestPath"])

# Define the PNG reader, and load the file

class imageData:
    def __init__(self, width, height, pixels, metadata, pixelList):
        self.width = width
        self.height = height
        self.pixels = pixels
        self.metadata = metadata
        self.pixelList = pixelList

pngReader = png.Reader(configFile["imagePath"])

width, height, pixels, metadata = pngReader.read()
image = imageData(width, height, pixels, metadata, list(pixels))


def getRowPixels(row, pixelList): # note, row 0 is top row
    return list(pixelList[row])

def getPixelLightness(column, rowPixels, metadata):
    planes = int(metadata.get("planes", 1))
    start = column * planes
    pixel = rowPixels[start:start + planes]

    if not pixel:
        return 0

    if len(pixel) >= 3:
        return int(sum(pixel[:3]) / 3)

    return int(pixel[0])

def getColumnPixels(column, height, pixelList): # note, column 0 is leftmost column
    columnPixels = []

    for y in range(height):
        columnPixels.append(pixelList[y][column])

    return columnPixels

def getSectionPixels(x, y, sideLength, image):
    sectionPixels = []

    maxY = min(y + sideLength, image.height)
    maxX = min(x + sideLength, image.width)

    for row in range(y, maxY):
        rowPixels = getRowPixels(row, image.pixelList)
        sectionRow = []
        for column in range(x, maxX):
            sectionRow.append(getPixelLightness(column, rowPixels, image.metadata))
        sectionPixels.append(sectionRow)

    return sectionPixels

def getSectionAverageLightness(sectionPixels):
    flatSection = [pixel for row in sectionPixels for pixel in row]
    if not flatSection:
        return 0
    return sum(flatSection) / len(flatSection)

def getCharacterRamp(characterLightnessMap):
    return [
        characterEntry[0]
        for characterEntry in sorted(
            characterLightnessMap.items(),
            key=lambda characterEntry: characterEntry[1],
        )
    ]

def mapLightnessToOrderedCharacter(lightness, minLightness, maxLightness, characterRamp, darkBias=0.7):
    if not characterRamp:
        return " "

    if maxLightness <= minLightness:
        return characterRamp[-1]

    normalizedLightness = (lightness - minLightness) / (maxLightness - minLightness)
    normalizedLightness = max(0.0, min(1.0, normalizedLightness))

    # Bias toward darker tones so dark regions get more visible differentiation.
    biasedLightness = normalizedLightness ** darkBias
    rampIndex = int(round(biasedLightness * (len(characterRamp) - 1)))
    return characterRamp[rampIndex]

def getCharacterTileSize(characterManifestMap, fallbackWidth, fallbackHeight):
    for characterPath in characterManifestMap.values():
        if characterPath and os.path.exists(characterPath):
            with Image.open(characterPath) as characterImage:
                return characterImage.size

    return (fallbackWidth, fallbackHeight)

def renderQuickPreview(asciiRows, characterManifestMap, outputPath, tileWidth, tileHeight):
    if not asciiRows:
        return

    rowCount = len(asciiRows)
    columnCount = max(len(row) for row in asciiRows)
    canvas = Image.new("L", (columnCount * tileWidth, rowCount * tileHeight), color=255)
    tileCache = {}

    for rowIndex, asciiRow in enumerate(asciiRows):
        for columnIndex, character in enumerate(asciiRow):
            characterPath = characterManifestMap.get(character)
            if not characterPath:
                continue

            if character not in tileCache:
                tileCache[character] = Image.open(characterPath).convert("L").resize((tileWidth, tileHeight))

            canvas.paste(tileCache[character], (columnIndex * tileWidth, rowIndex * tileHeight))

    canvas.save(outputPath)


sectionSideLength = int(configFile["sectionSideLength"])
characterRamp = getCharacterRamp(characterLightnessMap)
sectionAverageRows = []

for y in range(0, image.height, sectionSideLength):
    sectionAverageRow = []
    for x in range(0, image.width, sectionSideLength):
        section = getSectionPixels(x, y, sectionSideLength, image)
        sectionAverageLightness = getSectionAverageLightness(section)
        sectionAverageRow.append(sectionAverageLightness)

    sectionAverageRows.append(sectionAverageRow)

flatSectionAverages = [lightness for row in sectionAverageRows for lightness in row]
minSectionLightness = min(flatSectionAverages) if flatSectionAverages else 0
maxSectionLightness = max(flatSectionAverages) if flatSectionAverages else 255

asciiRows = []
for sectionAverageRow in sectionAverageRows:
    asciiRowCharacters = []
    for sectionAverageLightness in sectionAverageRow:
        asciiRowCharacters.append(
            mapLightnessToOrderedCharacter(
                sectionAverageLightness,
                minSectionLightness,
                maxSectionLightness,
                characterRamp,
            )
        )

    asciiRows.append("".join(asciiRowCharacters))

for asciiRow in asciiRows:
    print(asciiRow)

baseTileWidth, baseTileHeight = getCharacterTileSize(
    characterManifestMap,
    sectionSideLength,
    sectionSideLength,
)
outputScale = float(configFile.get("outputScale", 2.0))
tileWidth = max(1, int(round(baseTileWidth * outputScale)))
tileHeight = max(1, int(round(baseTileHeight * outputScale)))

renderQuickPreview(
    asciiRows,
    characterManifestMap,
    configFile.get("output", "output.png"),
    tileWidth,
    tileHeight,
)