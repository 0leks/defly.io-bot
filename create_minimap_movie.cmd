ffmpeg -r 16 -f image2 -s 485x485 -i ./combined/img%06d.png -vcodec libx264 -crf 18  -pix_fmt yuv420p combinedmovie.mp4
