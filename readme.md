# DragDropPDF

## Licence

AGPL-3.0 needed to add Ghostscript binary to DragDropPDf package

## About

Litte program that display a square on your destop, you can drag'n drop pdf files on it to reduce the size. You chan choose between 3 modes and change their settings for your needs.
It work with Ghostsript under AGPL-3.0 licence

## Installation

Run the setup or dezip the package

## Use it with python

Work with python 3.10

You'll need Ghostscript binary (unzip the setup) in `bin` folder

 - gsdll64.dll
 - gsdll64.lib
 - gswin64.exe
 - gswin64c.exe

> git clone https://github.com/yann83/DragDropPDF.git

> pip install -r requirements.txt

then run `interface.py` main

## How to Use

Right click on on the square

![low_level](./img/pdflow.jpg)

you can choose between 3 levels of compression :

 - HIGH for highest quality
 - LOW for lowest quality
 
From the contextual menu you can choose the output folder.

## Avanced configuration

you can edit the config.json file.

You will find the config.json file in the same location as the `DragDropPDF` executable, if the latter is in a location that requires privilege elevation then it will be here:

 > C:\Users\<username>\appdata\local\DragDropPDF

Here the default `config.json` content

`base_args` value is a list with Ghostscript default parameters for all profiles.<br>
Then you'll find `high`, `medium` and `low` profiles parameters. Each one have custom [Ghostscript parameters](https://ghostscript.readthedocs.io/en/latest/index.html).



```json
{
  "path": "C:/temp",
  "base_args": [
    "-sDEVICE=pdfwrite",
    "-dNOPAUSE",
    "-dQUIET",
    "-dBATCH",
    "-dCompatibilityLevel=1.4"
  ],
  "pics": {
    "high": "pdf.jpg",
    "medium": "pdfmedium.jpg",
    "low": "pdflow.jpg"
  },
  "current": {
    "low": "pdflow.jpg"
  },
  "high": {
    "dPDFSETTINGS": "/printer"
  },
  "medium": {
    "dPDFSETTINGS": "/ebook",
    "sColorConversionStrategy": "Gray",
    "dProcessColorModel": "/DeviceGray"
  },
  "low": {
    "dPDFSETTINGS": "/screen",
    "sColorConversionStrategy": "Gray",
    "dProcessColorModel": "/DeviceGray"
  }
}
```