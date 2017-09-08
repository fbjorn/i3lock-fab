## Fabulous wrapper over i3lock.  
Key differences:
 - ##### Set up random image as wallpaper every time you lock the computer
   By default it crawls random image from reddit's [r/wallpaper](https://www.reddit.com/r/wallpaper/)
 - ##### Enable multimonitor support  
   Background image fits correctly in all your monitors ecsaping ugly tiling  
   
### Requirements:
- i3lock
- ImageMagic  


```bash
sudo apt-get install imagemagick i3lock
```

### Installation:  
```bash
pip install i3lockfab
```

### Usage:  
Replace `i3lock` with `i3lock-fab` in your i3 config. e.g.:  
```bash
bindsym $mod+l exec "i3lock-fab"
```

### Configuration:
All the settings are located in `~/.i3lock-fab/conf.yaml`  
You can disable image randomizer or change the pictures origin



Thanks [@ShikherVerma](https://github.com/ShikherVerma) for idea with image resizing.
