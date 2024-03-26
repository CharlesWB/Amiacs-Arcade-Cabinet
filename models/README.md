# Models

This folder contains various "models" used to create the Amiacs arcade cabinet. Such as 3D models, artwork, and Fritzing diagrams.

## Amiacs Arcade Cabinet Prototype.skp

3D CAD model of the original prototype cabinet. Created using [SketchUp](https://www.sketchup.com/).

## Amiacs Arcade Cabinet v32.step

A STEP file format export of the CAD model prior to the removal of the export functionality from the personal version of AutoDesk Fusion 360. This export occurred at v32 of the Fusion 360 model.

## Amiacs Arcade.fzz

Fritzing diagram representing the wiring of all the components in the cabinet. Created using [Fritzing](https://fritzing.org/).

## Button Labels.svg

Vector images for the labels that are placed directly on the control panel buttons. Created using [Inkscape](https://inkscape.org/).

### Fonts Used

* [Game Played](https://www.dafont.com/game-played.font) for button text.
* [Restroom](https://www.dafont.com/restroom.font) for one and two player button labels (character 'G').
* [Fire](https://www.dafont.com/fire.font) for hotkey button symbol (character 't').

In Inkscape, Document Resources also has a list of the fonts used in the file.

### Usage

* Designed for import to [Cricut Design Space](https://cricut.com/) for cutting.
* Cut from black vinyl with adhesive backing.
* The circle of each label is used for aligning the text on the actual button.

*Cricut Design Space Import*

1. In Inkscape, select all text objects and use Path -> Object to Path.
    * Cricut Design Space didn't import text objects.
    * Use Ctrl to select into a group.
2. Upload as image to Cricut Design Space.
3. Change size of top level group to match Inkscape size.
    * Not sure why size is incorrect. Possibly due to metric/inch scaling.
    * Technically Inkscape size is .1 mm larger due to stroke thickness.
4. Ungroup top level group.
5. Select each button label group and Attach to keep the shapes together.

## Cabinet Artwork.svg

Vector image used for describing the cabinet graphics. Created using [Inkscape](https://inkscape.org/).

### Fonts Used

* [Game Played](https://www.dafont.com/game-played.font) for button text and console labels.
* [Fire](https://www.dafont.com/fire.font) for hotkey button symbol (character 't')
* [Aurebesh](https://www.dafont.com/aurebesh.font) for the secret names.
* [Back to the Future 2002](https://www.dafont.com/back-to-the-future.font) for the representation of the logo on the marquee. This is not meant to be the final look.
* Arial for drawing notes and reference dimensions.

In Inkscape, Document Resources also has a list of the fonts used in the file.

## Cabinet Labels.svg

Vector images of various labels placed on the cabinet. Created using [Inkscape](https://inkscape.org/).

### Fonts Used

* Arial for all text.

In Inkscape, Document Resources also has a list of the fonts used in the file.

### Usage

I'm using an adhesive backed vinyl. Trying to get the best durability and adhesion.

## Test Amiacs Light Controller.fzz

Fritzing breadboard diagram for testing the various LEDs of the cabinet. Created using [Fritzing](https://fritzing.org/).

## Test MCP23017 Arcade Button LEDs.fzz

Fritzing breadboard diagram for testing control of the button LEDs using an MCP23017. Created using [Fritzing](https://fritzing.org/).

This was an early prototype for controlling multiple LEDs using two pins on the Arduino. This is not used in the current cabinet design.
