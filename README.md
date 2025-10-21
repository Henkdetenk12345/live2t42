# live2t42
## How to use
Note: live2t42 outputs on stdout.


`python3 live2t42 [url] [pid]`


Example for NPO 1: `python3 live2t42 "http://192.168.1.9:9981/stream/channel/6e3100625cb75166d2a37d28306b978b?ticket=7496585080d775fa6fb85a4a9fb25e60a4839471" 0835`


## Use cases
If in use with vbit-iv use it like this: `python3 live2t42 "http://192.168.1.9:9981/stream/channel/6e3100625cb75166d2a37d28306b978b?ticket=7496585080d775fa6fb85a4a9fb25e60a4839471" 0835 | vbit-iv.py 1 0`
It can also be used with raspi-teletext to rebroadcast the teletext on the composite output of a Raspberry PI.
