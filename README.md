# DJ-Beatmatch-Encoder

This is a project I designed for personal use, though I figured it was worth uploading, both to explain the paradigm with DJ'ing and in case anyone shares my workflow.

When designing musical DJ sets to perform, I use the software 'Mixed In Key' to determine my music's fundamental key & the beats-per-minute (bpm) of each song

I also perform on CDJ's, many of which don't have 'sync' functions. This means you have to match the speed of each song manually with the BPM of the set.

Rather than doing this by ear, I realized there was a mathematical equation I could do to make a song the same speed as my DJ set.

This program takes all files in a specific folder, reads the BPM of the song, and then expresses what percentage higher or lower they would need to be to "match" the set's BPM.

The BPM reading appends to '03' as I usually preface my files with a number, for their order in the set (i.e. 01. Trackname)

The two variables worth noting for editting purposes are 'dj_directory' and 'base_bpm'. 

Currently, this project does not support nontraditional characters, though I may add support.

For this script to work properly, one has to make sure that they have the BPM of their track on the files.
