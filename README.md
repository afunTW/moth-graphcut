# moth-graphcut
An interactive application for moth graphcut, but only accept the source from [dearlep](http://dearlep.tw/)
## Usage

```
optional arguments:
  -h, --help            show this help message and exit
  -a, --all             process all image
  -i IMAGE [IMAGE ...], --image IMAGE [IMAGE ...]
                        process input image
  -r RECURSIVE [RECURSIVE ...], --recursive RECURSIVE [RECURSIVE ...]
                        process all image in given directory
```

**Example input image**

<img src="https://github.com/afunTW/moth-graphcut/raw/master/image/sample/3.jpg" alt="0" width="400">

**Example operation window**
![image/sample/3.jpg](https://user-images.githubusercontent.com/4820492/28349942-5a76d20c-6c78-11e7-92cf-d7141bbb8917.png)

- black tracking label present the seperate part
- red tracking label present the elimination
- gamma track bar present the adjustment of image brightness that my useful for light color or transparent moth
- threshold track bar present the threshold for mask
- Press 'h' to get others functionalities

Press SPACE to save the image result:

- new directory at the same place of image path
  - 5 components saved in rgba png with transparent background 
  - metadata json
- overview screen shot at the `moth-graphcut/metadata/`

## Metadata format
The program will create a metadata directory and save image metadata per image with hash filename. And there will be another file named `map.json` to map the image to hash file name and the state of image. If user run the program again, it will check the image history from map.json then roll back.

**metadata json format**
```
{
  "name": [image original absolute path],
  "mirror_line": [[x1, y1], [x2, y2]],
  "mirror_shift": int,
  "threshold": int,
  "state": "...",
  "tracking_label": {
    "right": [[x1, y1], [x2, y2], ...],
    "eliminate": [...],
    "left": [...]
  },
  "component_contour": {
    "body": [[coordinate y], [coordinate x]],
    "forewings": {
      "right": [...],
      "left": [...]
    },
    "backwings": {
      "right": [...],
      "left": [...]
    }
  },
  "component_color": {
    "body": [[R1, G1, B1], [R2, G2, B2], ...],
    "forewings": {
      "right": [...],
      "left": [...]
    },
    "backwings": {
      "right": [...],
      "left": [...]
    }    
  }
}
```

## Cited By
* demo images from [dearlep](http://dearlep.tw/)
* interactivate grabcut from [opencv](https://github.com/opencv/opencv/blob/master/samples/python/grabcut.py)
