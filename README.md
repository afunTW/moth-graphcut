# moth-graphcut
An interactive app to do graph cut with moth images

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

<img src="https://github.com/afunTW/moth-graphcut/raw/master/image/sample/7.jpg" alt="0" width="400">

**Example operation window**
![image](https://user-images.githubusercontent.com/4820492/27267443-fcf0f036-54da-11e7-89ac-1e5145f560e8.png)

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
