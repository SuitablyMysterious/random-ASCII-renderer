import argparse
import json
import os

from PIL import Image, ImageDraw, ImageFont


def readConfig(configPath):
    with open(configPath, "r") as cfg:
        return json.load(cfg)


def generateManifest(manifestPath, charList, outputDir):
    manifestMap = {}
    for i, char in enumerate(charList):
        manifestMap[char] = os.path.join(outputDir, f"{i}.png")

    with open(manifestPath, "wt") as manifest:
        json.dump(manifestMap, manifest, indent=2)

    return manifestMap


def loadFont(path, size):
    return ImageFont.truetype(path, size=size)


def renderChar(char, outputPath, font, width, height, fg, bg):
    image = Image.new("L", (width, height), color=bg)
    draw = ImageDraw.Draw(image)

    bbox = draw.textbbox((0, 0), char, font=font)
    glyphWidth = bbox[2] - bbox[0]
    glyphHeight = bbox[3] - bbox[1]
    x = (width - glyphWidth) // 2 - bbox[0]
    y = (height - glyphHeight) // 2 - bbox[1]

    draw.text((x, y), char, fill=fg, font=font)
    image.save(outputPath)

def generateLightness(manifestMap, charList):
    lightnessMap = {}

    for charName in charList:
        image = Image.open(manifestMap[charName]).convert("L")
        pixels = image.get_flattened_data()
        averageLightness = sum(pixels) / len(pixels)
        lightnessMap[charName] = averageLightness

    with open("lightness.json", "wt") as lightnessFile:
        json.dump(lightnessMap, lightnessFile, indent=2)



def main():
    parser = argparse.ArgumentParser()

    parser.add_argument("--config", default="config.json")
    parser.add_argument("--font", default=None)
    parser.add_argument("--manifest", default="manifest.json")

    arguments = parser.parse_args()

    config = readConfig(arguments.config)
    charList = config.get("chars") or config.get("characters") or []


    scriptDir = os.path.dirname(os.path.abspath(__file__))
    defaultFontPath = os.path.join(scriptDir, "..", "fonts", "MonaspaceXenonFrozen-WideRegular.ttf")
    outputDir = config.get("outputDir", scriptDir)

    fontPath = arguments.font or config.get("fontPath", defaultFontPath)
    fontSize = int(config.get("fontSize", 64))
    width = int(config.get("width", 64))
    height = int(config.get("height", 64))
    fg = int(config.get("foreground", 255))
    bg = int(config.get("background", 0))

    os.makedirs(outputDir, exist_ok=True)

    font = loadFont(fontPath, fontSize)
    manifestMap = generateManifest(arguments.manifest, charList, outputDir)

    for char in charList:
        renderChar(char, manifestMap[char], font, width, height, fg, bg)
    
    generateLightness(manifestMap, charList)

if __name__ == "__main__":
    main()